The one thing to understand first: there is no internal wallet

FreelanceFlow does not store money in user balances. Real rupees only ever live in two places:

Razorpay's side — the platform's Razorpay account holds captured funds; RazorpayX pushes them out to the freelancer's real bank account.
Your database — only accounting records of that money (who paid, how much, what state it's in). These are the ledger, not the money itself.

The "escrow" is a database status, not a separate bank account. When money is "in escrow," it is physically sitting in the platform's Razorpay balance, and the DB has a row saying "this ₹X is earmarked for this contract, not yet released."

The ledger tables (models.py, models_milestone.py):

Table	What it records
Payment	The money-movement state machine + Razorpay IDs (order_id, payment_id, payout_id, refund_id) + total_amount
Escrow	held_amount, released_at — the "funds are being held" marker
PlatformEarning	The platform's 10% cut per payment (revenue tracking)
PaymentMilestone	Per-stage status: PENDING → IN_PROGRESS → SUBMITTED → APPROVED → PAID
PaymentEvent	Webhook idempotency log (dedupes Razorpay double-deliveries)

Payment.Status: PENDING → ESCROWED → PAYOUT_PENDING → RELEASED (plus PAYOUT_FAILED, REFUNDED).

Stage 1 — Client adds money (escrow is created)

Endpoint: POST /api/payments/milestones/{id}/fund/ → PaymentMilestoneViewSet.fund → create_milestone_escrow(contract, client, milestone) in services.py.
(Legacy alternative: POST /api/payments/escrow/ → create_escrow funds the whole contract.agreed_amount in one shot. Same models, no milestone split.)

What it does:

Authorizes: contract.client == client (else PermissionDeniedError), milestone belongs to the contract, no existing payment on it.
Creates a Razorpay Order: {'amount': int(milestone.amount * 100), 'currency': 'INR', 'receipt': 'milestone_{id}', ...} — amount is in paise (×100).
Creates a local Payment(status=PENDING, razorpay_order_id=..., total_amount=milestone.amount).
Returns the razorpay_order_id + amount to the frontend, which opens the Razorpay checkout so the client actually pays with a card/UPI/netbanking.

At this point no money has moved and nothing is held yet — status is just PENDING.

Stage 2 — Client pays → money is captured & "held in escrow"

After the client completes the Razorpay checkout, the payment is confirmed by either of two paths (both land on the same function):

Frontend callback: POST /api/payments/verify/ → verify_payment (views.py) → verify_razorpay_signature(order_id, payment_id, signature) (HMAC-SHA256 of "{order_id}|{payment_id}" with the secret) → confirm_escrow_payment(...).
Server-to-server webhook: POST /api/payments/webhook/ → razorpay_webhook → process_razorpay_webhook (verifies webhook signature, checks idempotency) → dispatches process_razorpay_webhook_task (tasks.py) → on payment.captured → confirm_escrow_payment(...).

confirm_escrow_payment(order_id, payment_id) — this is the "money is now held" step:

Locks the Payment row (select_for_update), which must be PENDING.
Flips it to ESCROWED and saves the razorpay_payment_id.
Creates the Escrow row with held_amount = total_amount. ← this row is what "in escrow" means.
If it's a milestone, sets the milestone to IN_PROGRESS (this is the signal that the freelancer may now work).
On commit, notifies the freelancer: "Escrow created — money is secured, start work."

Where the money physically is now: in the platform's Razorpay account. The DB rows (Payment=ESCROWED + Escrow.held_amount) are the promise that this money is reserved for this freelancer and hasn't been released.

Stage 3 — Freelancer submits the deliverable

Endpoint: POST /api/payments/milestones/{id}/complete/ → PaymentMilestoneViewSet.complete → complete_milestone(...) in services_milestone.py.

Authorizes: milestone.contract.bid.freelancer == user.
Requires the milestone be IN_PROGRESS — i.e. the client must have already funded it. A freelancer cannot submit against an unfunded milestone.
Saves deliverable_description + deliverable_files (JSON list), sets status to SUBMITTED, stamps submitted_at.
Pushes a websocket event (milestone_submitted) and notifies the client that a deliverable is waiting for review.

No money moves here — it's still sitting in escrow.

Stage 4 — Client approves → release is triggered

Endpoint: POST /api/payments/milestones/{id}/release/ → PaymentMilestoneViewSet.release → release_milestone_payment(milestone_id, client).

Authorizes: milestone.contract.bid.project.client == client.
Milestone must be SUBMITTED/APPROVED and not yet PAID; the linked Payment must be ESCROWED.
Marks the milestone APPROVED (approved_by, approved_at).
Calls release_payment(contract, client, payment_id=payment.id) — the actual money-out step.
Stage 5 — Money goes to the freelancer (payout)

release_payment(...) in services.py computes the split and then takes one of two paths depending on config:

Platform cut via calculate_platform_cut(total, PLATFORM_CUT_PERCENTAGE) (core/utils.py): default 10% to the platform, so freelancer_amount = total − cut (freelancer gets ~90%), rounded to the paisa (ROUND_HALF_UP).

Real path (production, when Razorpay keys are live, the freelancer has a razorpay_fund_account_id, and RAZORPAY_ACCOUNT_NUMBER is set):

Sets Payment.status = PAYOUT_PENDING.
On commit, dispatches razorpay_transfer_to_freelancer_task(payment.id, freelancer_amount) (tasks.py).
That task calls RazorpayX payout.create(...) — an actual IMPS bank transfer from the platform's RazorpayX account to the freelancer's registered bank account (fund_account_id), amount in paise, mode='IMPS'.
On success (atomic): Payment.status = RELEASED, saves razorpay_payout_id, creates PlatformEarning (the 10%), sets escrow.released_at, closes the contract (is_active=False, end_date), marks the project completed, and flips the milestone to PAID (paid_at).
Notifies the freelancer (PAYMENT_RELEASED) and generates a delivery proof.
On failure it retries up to 3×, then sets PAYOUT_FAILED with the error.

Simulation path (local/dev, when keys are placeholders, or there's no fund account / account number): does all of the same DB state changes synchronously and stamps razorpay_payout_id = "payout_mock_simulated" — so the whole flow works end-to-end without real Razorpay credentials.

⚠️ Known bug on the confirmation step (H4 in BUGS.md): after a real payout, Razorpay sends a payout.processed webhook that's supposed to do a final "confirmed landed" update — but that handler references Payment.Status.PAID, which doesn't exist in the enum, so it throws AttributeError. The freelancer is already paid and the payment is already RELEASED; only this extra confirmation status update crashes. Documented, not fixed (per your instruction).

The complete chain in one line
Client funds → Razorpay Order (PENDING)
  → client pays → payment.captured / verify → ESCROWED + Escrow row  [money held in platform's Razorpay balance]
  → freelancer submits → milestone SUBMITTED
  → client approves → release_milestone_payment → release_payment
  → RazorpayX IMPS payout (real) or simulated → RELEASED + milestone PAID  [money lands in freelancer's bank]
     platform keeps 10% (PlatformEarning), freelancer gets 90%

Money storage, summarized:

Before release: platform's Razorpay account balance (DB says ESCROWED + Escrow.held_amount).
After release: freelancer's real bank account via RazorpayX IMPS (DB says RELEASED, milestone PAID, escrow.released_at set).
Platform's 10%: stays in the platform's Razorpay balance, recorded as a PlatformEarning row.
Your database never holds money — only the state of it.

Milestones each carry an explicit amount (constrained so all milestones sum to ≤ contract.agreed_amount) and are funded and released independently, each getting its own Payment + Escrow. The legacy path escrows the full contract amount as a single payment instead.