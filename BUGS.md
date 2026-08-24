# FreelanceFlow — Bug Report (End-to-End Audit)




**Totals:** 0 CRITICAL · 15 HIGH · 15 MEDIUM · 14 LOW · 1 cross-cutting theme.


## 🟠 HIGH

### H1 — [FIXED] `ValidationError(code=...)` raises `TypeError` → 500; email verification 500s on **every** call
- **Location:** `core/exceptions.py:100` (`ValidationError.__init__`), `apps/users/services/services.py`, `apps/users/models/models.py`.
- **Bug Fixed:** Added a `code` parameter to `ValidationError.__init__`. Implemented Option B model for email verification by adding `is_email_verified` to the User model, leaving `is_active=True` as default, and updating the email verification flow to verify `is_email_verified` instead of `is_active`.
- **Outcome:** Verified email successfully marks `is_email_verified = True` in DB. Duplicate verification and invalid reset tokens correctly return clean `400` validation errors with proper machine-readable error codes.

### H2 — [FIXED] Login defaults an unknown role to `FREELANCER` *(Issue #7)*
- **Location:** `frontend/src/pages/auth/AuthPage.jsx:100`, `:122`; `frontend/src/pages/auth/GoogleCallbackPage.jsx:43`, `:50`
- **Bug Fixed:** Added validation checks during authentication redirect/routing. If the user's role is missing or undefined, it throws an error/redirects back to the login page with an authentication error instead of silently falling back and dropping them into the freelancer UI.
- **Outcome:** Authenticated users are safely and correctly routed matching their actual stored role; no silent "everyone is a freelancer" fallback occurs.

### H3 — [FIXED] Google OAuth callback error path strands the user on the login page *(Issue #8, second cause)*
- **Location:** `frontend/src/pages/auth/GoogleCallbackPage.jsx:48`
- **Bug Fixed:** Handled OAuth error branch and profile fetch failure. If token validation or user profile fetching fails during callback processing, the page redirects the user to the login view with an error banner instead of attempting to route them to a protected dashboard route (which would cause the route guards to eject them back to the login page without error feedback).
- **Outcome:** Google OAuth failures gracefully redirect the user back to the login screen with a clear error prompt rather than stranding them on a frozen screen.


### H4 — [FIXED]`Payment.Status.PAID` does not exist → `payout.processed` webhook always crashes
- **Location:** `apps/payments/tasks.py:69`, `:71`; enum at `apps/payments/models/models.py:10`
- **Bug:** The `payout.processed` branch does `.exclude(status=Payment.Status.PAID).update(status=Payment.Status.PAID, ...)`, but `Payment.Status` defines only `PENDING/ESCROWED/PAYOUT_PENDING/RELEASED/PAYOUT_FAILED/REFUNDED` — there is **no `PAID`** member (only `PaymentMilestone.Status` has `PAID`). This branch has no try/except, so every Razorpay `payout.processed` webhook raises `AttributeError` and the task dies; payments can never be recorded as settled.
- **Fix:** Use an existing terminal state (`Payment.Status.RELEASED`) here, or add a real `PAID = "PAID", "Paid"` member to `Payment.Status` **with a migration** and use it consistently. Wrap the branch in the same defensive try/except used by `payment.captured`.
- **Expected outcome:** `payout.processed` webhooks succeed and mark the payment settled; the payout lifecycle reaches its terminal state instead of throwing.

### H5 — [FIXED] Destructive IDOR: `clear_milestones` wipes any pre-funding contract's milestones
- **Location:** `apps/payments/views/views_extended.py:39`
- **Bug Fixed:** Added a permission check validating if `contract.bid.project.client == request.user`. Only the owning client who created the project and bid contract can clear the milestones.
- **Outcome:** Non-owners attempting to clear a contract's milestones are rejected with a clean `403 Forbidden` response.

### H6 — [FIXED] Write IDOR: `create_milestone` injects milestones into any contract
- **Location:** `apps/payments/views/views_extended.py:53` → `apps/payments/services/services_milestone.py:15`
- **Bug Fixed:** Modified `create_milestone` to accept the requesting `user` instance and validate that `contract.bid.project.client == user`. Wrapped the milestone check query using `select_for_update()` to enforce concurrency checks and prevent overshooting the `agreed_amount`.
- **Outcome:** Non-owners are prevented from creating/injecting milestones into third-party contracts, and milestone total amount checks are protected against race conditions. 

### H7 — [FIXED] Skill matching is AND-chained and case-sensitive → "no suggestions" *(Issue #1)*
- **Location:** `apps/search/views/views.py:289` (and `:101`)
- **Bug Fixed:** Refactored database fallback query logic to match skills case-insensitively and using OR semantics. It fetches the profiles and uses a Python-side `any()` check to verify matches.
- **Outcome:** Freelancers matching **any** requested skill are successfully suggested/returned, regardless of capitalization, resolving the empty recommendations bug.

### H8 — [FIXED] Elasticsearch `terms` query on a case-sensitive keyword field
- **Location:** `apps/search/views/views.py:270`
- **Bug Fixed:** Configured a custom `lowercase_normalizer` analyzer inside the Elasticsearch index settings for both `ProjectDocument` and `FreelancerDocument` in `apps/search/documents.py`. Applied this normalizer to the `skills` KeywordFields, and updated query parameters inside `views.py` to be lowercased before execution.
- **Outcome:** Elasticsearch-based skill matching correctly searches skills case-insensitively and returns expected matched freelancers.

### H9 — [FIXED] Search queries/orders reference non-existent model fields → `FieldError`/500
- **Location:** `apps/search/views/views.py:62`, `:232` (`required_skills`); `apps/search/services/services_autocomplete.py:10` (`frequency`)
- **Bug Fixed:** Updated DB search fallback queries in `views.py` to correctly query project skills via relation lookup (`skills__skill_name__icontains=skill`) instead of `required_skills`. Additionally fixed suggestions autocomplete ordering in `services_autocomplete.py` by referencing the correct `popularity` field instead of `frequency`.
- **Outcome:** Projects skill queries and search suggestions autocomplete execute cleanly without throwing `FieldError` or 500 exceptions.
 
### H10 — [FIXED] Async agent coroutine never awaited → 500 on chat + generate-deliverable
- **Location:** `apps/worklogs/services/services.py:477`, `:506`
- **Bug Fixed:** Wrapped both unawaited coroutine calls to `run_ai_worklog_agent` using `async_to_sync` (imported inline from `asgiref.sync`) so that they are correctly awaited and resolved.
- **Outcome:** The AI chat-message and generate-deliverable endpoints execute the agent synchronously and return responses cleanly without 500 error crashes.

### H11 — `approve_deliverable` violates `unique_together(contract, date)`
- **Location:** `apps/worklogs/services/services.py:329`
- **Bug:** `approve_deliverable` calls `WorkLog.objects.create(...)` unconditionally; a second approval on the same day for the same contract hits the `unique_together` constraint → `IntegrityError`/500.
- **Fix:** Use `update_or_create(contract=..., date=..., defaults={...})`, or guard for the existing row before creating.
- **Expected outcome:** Repeated same-day approvals update the existing worklog instead of crashing.

### H12 — Azure upload failure emails a fake `placeholder-azure-blob-url` as the real report
- **Location:** `apps/worklogs/services/pdf_service.py:90`
- **Bug:** On an Azure upload exception the code returns `https://placeholder-azure-blob-url/...`; the caller emails that link to the client and marks the report "sent," with no retry. The client receives a dead link presented as a delivered report.
- **Fix:** Treat an upload failure as a hard failure — raise/return an error, do not mark the report sent, and retry (Celery `retry`) or queue for manual follow-up. Never substitute a placeholder URL for a real artifact.
- **Expected outcome:** A failed upload leaves the report un-sent and retried; clients only ever receive working links.

### H13 — Bid update has no ownership check
- **Location:** `apps/bidding/views/views.py:74`
- **Bug:** The bid update path doesn't verify the requester owns the bid, allowing edits to another freelancer's bid.
- **Fix:** Enforce `bid.freelancer == request.user` (via `get_queryset` filtering and/or an object permission) before allowing update.
- **Expected outcome:** Freelancers can only edit their own bids; others get 403/404.

### H14 — Contract completion transitions to `TERMINATED`; `COMPLETED` is unreachable + duplicate-contract path
- **Location:** `apps/bidding/services/services.py:405` (complete → `TERMINATED`), `models.py:91`; accept path `services.py:139`, `:224`
- **Bug:** `complete_contract` sets the status to `TERMINATED`, so the `COMPLETED` state can never be reached. The accept-bid path can also create duplicate contracts / accept multiple bids for one project.
- **Fix:** Set the terminal state to `COMPLETED` in `complete_contract`. In the accept path, guard with `select_for_update` + a uniqueness check so only one bid can be accepted and only one contract created per project.
- **Expected outcome:** Completed contracts read `COMPLETED`; a project yields exactly one accepted bid and one contract.

### H15 — Production WebSockets broken: `InMemoryChannelLayer` across workers
- **Location:** `config/settings/base.py:217`; not overridden in `config/settings/production.py`
- **Bug:** `CHANNEL_LAYERS` uses `channels.layers.InMemoryChannelLayer` (the comment falsely says "Upstash Redis"), and production doesn't override it. In-memory layers are per-process, so with multiple Daphne/Gunicorn workers, chat messages and notification broadcasts only reach clients connected to the same worker.
- **Fix:** In production use `channels_redis.core.RedisChannelLayer` pointed at `REDIS_URL`. Keep `InMemoryChannelLayer` only in `local.py`.
- **Expected outcome:** Real-time chat and notifications are delivered to all connected clients regardless of which worker serves the socket.

---

## 🟡 MEDIUM

### M1 — Freelancer "total earned" is gross, not net *(Issue #14)*
- **Location:** `apps/payments/selectors.py:42` (`get_freelancer_total_earned`), `:30` (`get_freelancer_earnings`)
- **Bug:** Sums `total_amount` (the full escrow amount) even though the freelancer receives `total − platform_cut`. On a ₹1,000 contract at 10% they receive ₹900 but "total earned" shows ₹1,000. The commission is never surfaced.
- **Fix:** Report net earnings (`total_amount − cut_amount`, e.g. join/subtract `PlatformEarning`), and expose the platform cut explicitly on the payment/earnings serializers so the UI can show the deduction.
- **Expected outcome:** Earnings reflect what the freelancer actually received, and the commission is visible on the payment page.

### M2 — Generic `release` 500s (`MultipleObjectsReturned`) on milestone contracts
- **Location:** `apps/payments/views/views.py:120` → `apps/payments/services/services.py:268`
- **Bug:** `release_payment` does `Payment.objects.select_for_update().get(contract=contract)`, but a milestone contract has many `Payment` rows; only `Payment.DoesNotExist` is caught, so `MultipleObjectsReturned` propagates as a 500.
- **Fix:** Require a `payment_id` (or `milestone_id`) on the release endpoint, or catch `MultipleObjectsReturned` and return a 400 directing the caller to the per-milestone release.
- **Expected outcome:** Releasing on a milestone contract targets a specific payment and returns a clean response instead of 500.

### M3 — Profile image uploaded twice per submit + no request timeout *(Issue #6)*
- **Location:** `frontend/src/pages/freelancer/FreelancerOnboardingPage.jsx:673` (and `:116`); `frontend/src/api/axiosConfig.js:3`
- **Bug:** Avatar/banner are uploaded twice on a single submit, and axios has no request timeout, so a slow/hung upload appears "stuck" indefinitely.
- **Fix:** Upload each image once (dedupe the submit handler / guard against double-fire), and set a sensible axios `timeout` with a user-visible error on timeout.
- **Expected outcome:** One upload per image; a slow upload fails with a clear message instead of hanging forever.

### M4 — Read receipts fire on socket delivery, not on viewing *(Issue #11)*
- **Location:** `apps/messaging/consumers.py:290`
- **Bug:** Messages are marked "read" when delivered over the socket, not when the recipient actually views them, so read receipts are inaccurate.
- **Fix:** Mark read only on an explicit client "message viewed / conversation opened" event, not on delivery.
- **Expected outcome:** Read receipts reflect actual viewing.

### M5 — NotificationBell links to non-existent routes → ejected to landing
- **Location:** `frontend/src/components/common/NotificationBell.jsx:69`
- **Bug:** Clicking a notification navigates to routes that don't exist (`/messages`, `/contracts`, `/earnings`); the catch-all route sends the user back to the landing page.
- **Fix:** Point each notification type at a real, role-prefixed route (e.g. `/freelancer/messages`, `/client/contracts`).
- **Expected outcome:** Clicking a notification lands on the correct page.

### M6 — Concurrent 401s each trigger their own token refresh (no mutex)
- **Location:** `frontend/src/api/axiosConfig.js:28`
- **Bug:** When several requests 401 at once, each fires its own refresh call; with refresh-token rotation this can invalidate tokens and log the user out.
- **Fix:** Serialize refresh with a single in-flight promise; queue pending requests and replay them once the one refresh resolves.
- **Expected outcome:** One refresh per expiry burst; no spurious logouts under concurrent requests.

### M7 — Regex HTML sanitizer is bypassable and used on content that renders as HTML
- **Location:** `core/sanitizers.py`; used with `allow_basic_formatting=True` in `apps/bidding/serializers/serializers.py:71`, `serializers_review.py:57`/`:101`, `apps/projects/serializers/serializers.py:109`/`:113`/`:141`/`:147`
- **Bug:** The regex sanitizer can be bypassed (e.g. `<b/onmouseover=alert(1)>` keeps its handler because the attribute-stripping regex requires whitespace after the tag name). This content flows into generated PDFs/emails → stored-XSS risk in HTML contexts.
- **Fix:** Replace the regex approach with a vetted sanitizer (`nh3`/`bleach`) with an explicit tag/attribute allow-list.
- **Expected outcome:** Malicious markup is neutralized regardless of formatting tricks; user content is safe to render as HTML.

### M8 — Insecure `SECRET_KEY` default
- **Location:** `config/settings/base.py:15`
- **Bug:** `SECRET_KEY` defaults to `"change-me-in-production"`, so a missing env var in production silently runs with a known key (session/CSRF/token forgery).
- **Fix:** Remove the insecure default — require `SECRET_KEY` and fail fast if unset in production.
- **Expected outcome:** Production refuses to boot without a real secret key.

### M9 — Duplicate handler / route double-registration shadowing
- **Location:** `apps/projects/views/views_extended.py:27` (duplicate `bookmark` — only DELETE registers, POST is shadowed); `apps/notifications/urls/urls.py:5` (double registration)
- **Bug:** A duplicate method definition and a double URL registration cause one handler to shadow the other, so an expected verb/route silently doesn't work.
- **Fix:** Remove the duplicate definition; register each route once with the intended methods.
- **Expected outcome:** Bookmark POST and the affected notification routes work as intended.

### M10 — `int(pk)` on a non-numeric path segment → 500
- **Location:** `apps/notifications/views/views.py:52`, `:70`
- **Bug:** The view calls `int(pk)` directly; a non-numeric `pk` raises `ValueError` (500) instead of a 404.
- **Fix:** Use a numeric URL converter (`<int:pk>`) or validate/`get_object_or_404`.
- **Expected outcome:** A bad id returns 404, not 500.

### M11 — Search rejects skills-only requests (`q` required)
- **Location:** `apps/search/serializers/serializers.py:33`
- **Bug:** `q` is `required=True`, so a request that filters only by skills (no free-text query) is rejected.
- **Fix:** Make `q` optional (`required=False`, default empty) and allow skills-only searches.
- **Expected outcome:** Clients can search by skills alone.

### M12 — Draft project uses a non-existent field and drops skills on publish
- **Location:** `apps/projects/services/services_draft.py:10`
- **Bug:** `draft_data` is treated as a model field but isn't one, and `publish_draft` doesn't copy skills onto the published project.
- **Fix:** Persist draft payloads in a real field (e.g. a JSON column) and copy skills through to the published project on publish.
- **Expected outcome:** Drafts save and publish with their skills intact.

### M13 — Message sender serialized inconsistently between REST and WebSocket
- **Location:** `apps/messaging/serializers/serializers.py:7` vs `apps/messaging/consumers.py:166`
- **Bug:** REST serializes `sender` as a full object; the WebSocket path emits a slim dict, so the frontend receives two different shapes for the same field and can mis-render "who sent this."
- **Fix:** Emit one canonical sender shape from both paths (share a serializer/helper).
- **Expected outcome:** Message sender data is identical over REST and WS; message attribution renders consistently.

### M14 — Bid state transitions: rejects WITHDRAWN bids and un-rejects manual rejections
- **Location:** `apps/bidding/services/services.py:224`, `:317`
- **Bug:** The accept/reject bulk transitions include `WITHDRAWN` bids in a reject sweep and can flip a manually-rejected bid back, muddying bid state.
- **Fix:** Exclude terminal states (`WITHDRAWN`, already-`REJECTED`) from bulk transitions; only auto-reject bids that are still `PENDING`.
- **Expected outcome:** Withdrawn/rejected bids keep their terminal state; only pending bids are auto-rejected on accept.

### M15 — DEBUG-only CORS wildcard with credentials
- **Location:** `core/middleware.py:70`
- **Bug:** In DEBUG, `SecurityHeadersMiddleware` sets `Access-Control-Allow-Origin: *` while `CORS_ALLOW_CREDENTIALS=True` — an invalid/unsafe combination that can mask real CORS behavior during development.
- **Fix:** Echo the specific request origin (as `CORSCustomMiddleware` already does) instead of `*` when credentials are enabled.
- **Expected outcome:** Dev CORS behaves like production (specific origin), avoiding false-positive/negative CORS results.

---

## 🟢 LOW

### L1 — Registration 500s when `role` is omitted
- **Location:** `apps/users/views/views.py:56` (`RegisterView.create`)
- **Bug:** `User.role` has a model default, so DRF makes the serializer field `required=False` **without** setting a serializer default. The view then does `serializer.validated_data['role']` → `KeyError`/500 when `role` isn't sent.
- **Fix:** Read it safely (`validated_data.get('role')`) and validate/normalize, or set an explicit serializer default and make the field required at the API level.
- **Expected outcome:** A registration request missing `role` returns a clean 400, not a 500.

### L2 — `SecurityHeadersMiddleware` sets an invalid comma-joined `Access-Control-Allow-Origin`
- **Location:** `core/middleware.py:73`
- **Bug:** In production it sets `Access-Control-Allow-Origin` to `", ".join(CORS_ALLOWED_ORIGINS)` — not a valid ACAO value (must be a single origin or `*`). Likely masked by `corsheaders`, but wrong.
- **Fix:** Remove the ACAO logic from this middleware and let `corsheaders` own CORS, or echo the single matched request origin.
- **Expected outcome:** A single valid ACAO header per response.

### L3 — Refund money math: truncated paise + misplaced `.quantize()`
- **Location:** `apps/payments/services/services.py:502`, `:526`, `:590`
- **Bug:** Refund amount is passed as `float` and the gateway amount computed as `int(refund_amount * 100)` (e.g. `int(0.29*100) == 28`), under-refunding by a paise for certain cents. Separately, `.quantize()` at `:502` binds to the percentage ratio, not the final amount, so the refund is never rounded to cents. (The freelancer **payout** path is safe — it re-wraps with `int(Decimal(str(amount)) * 100)`.)
- **Fix:** Keep money as `Decimal` end-to-end; compute `int(Decimal(str(refund_amount)) * 100)` and quantize the whole amount: `(total_amount * Decimal(str(pct)) / Decimal('100')).quantize(Decimal('0.01'), ROUND_HALF_UP)`.
- **Expected outcome:** Refunds are exact to the paise and reconcile with escrow/payout/platform-cut totals.

### L4 — Dead cache module; `delete_pattern` would crash on the LocMem cache
- **Location:** `core/cache.py`
- **Bug:** `CacheService` / `cached` / `invalidate_*` / `delete_pattern` have **no callers** anywhere in `apps/`, so the documented caching layer is effectively dead. `delete_pattern` is django-redis-only and would `AttributeError` on the LocMem "axes" cache if it were ever called.
- **Fix:** Either wire the cache layer in where it's intended, or remove it. If kept, guard `delete_pattern` for non-redis backends.
- **Expected outcome:** No dead/misleading caching code; no latent crash path.

### L5 — Unwired middleware/throttles
- **Location:** `core/middleware.py:80` (`RateLimitMiddleware` not in `MIDDLEWARE`); `core/throttles.py` (`LoginRateThrottle`/`TieredRateThrottle` unused)
- **Bug:** `RateLimitMiddleware` is defined but never added to `MIDDLEWARE`; the custom login throttles are never referenced. (Brute-force protection is actually handled by django-axes, which is enabled.)
- **Fix:** Remove the dead classes, or wire them if intended. Document that Axes is the real brute-force control.
- **Expected outcome:** No misleading "we rate-limit here" code; the actual protections are clear.

### L6 — Celery time limits inconsistent
- **Location:** `config/settings/base.py:275` (30/25 min) vs `config/celery.py` `app.conf.update` (10/5 min)
- **Bug:** `config/celery.py` overrides the settings-level limits, so the effective hard/soft limits are 10/5 min — long AI report / PDF tasks may be killed at 10 minutes unexpectedly.
- **Fix:** Pick one source of truth for time limits and align them to the slowest legitimate task.
- **Expected outcome:** Long report/PDF tasks aren't killed prematurely; limits are predictable.

### L7 — `isMe` inferred from the other party, not the current user
- **Location:** `frontend/src/pages/client/ClientMessagesPage.jsx:566`; `frontend/src/pages/freelancer/FreelancerMessagesPage.jsx`
- **Bug:** Message-bubble alignment ("is this mine?") is derived from the other participant rather than the logged-in user, which can misalign bubbles in edge cases.
- **Fix:** Compare `message.sender.id === currentUser.id`.
- **Expected outcome:** Own messages always align correctly.

### L8 — Request log `user_id` is always null for JWT API requests
- **Location:** `core/middleware.py:33`
- **Bug:** `RequestLoggingMiddleware` reads `request.user` (Django auth), which is `AnonymousUser` for DRF-JWT-authenticated API requests (JWT auth runs inside DRF, after this middleware). So `user_id` is always null in request logs.
- **Fix:** Resolve the user from the JWT in the middleware, or log `user_id` from within DRF (e.g. a DRF-level logging hook).
- **Expected outcome:** API request logs carry the real authenticated `user_id`.

### L9 — Worklog re-emails on missed report cycles; Qdrant reports success unconditionally
- **Location:** `apps/worklogs/tasks.py:185`; `apps/worklogs/services/qdrant_service.py:317`
- **Bug:** On missed report cycles the task can re-send emails for past periods; `is_initialized` is computed as `success or True`, which is always truthy and hides real init failures.
- **Fix:** Advance/track the last-processed cycle so past periods aren't re-emailed; set `is_initialized = bool(success)`.
- **Expected outcome:** No duplicate historical report emails; Qdrant init status reflects reality.

### L10 — LLM JSON parser crashes on non-dict JSON / non-numeric hours
- **Location:** `apps/worklogs/services/ai_service.py:368`
- **Bug:** The parser assumes the LLM returns a dict with numeric `hours`; a list/scalar JSON or a non-numeric hours value raises and bubbles up.
- **Fix:** Validate the parsed shape (dict check, numeric coercion with fallback) before use.
- **Expected outcome:** Malformed LLM output degrades gracefully instead of 500ing the flow.

### L11 — Azure SAS generation assumes an account-key credential
- **Location:** `apps/worklogs/services/pdf_service.py:73`
- **Bug:** SAS generation reads `blob_service.credential.account_key`, which only exists for connection-string/account-key auth; other credential types (e.g. managed identity) would break it.
- **Fix:** Detect the credential type and use user-delegation SAS when there's no account key.
- **Expected outcome:** SAS links work regardless of the configured Azure credential type.

### L12 — Missing project validation (past deadline / empty skills)
- **Location:** `apps/projects` create/validation path
- **Bug:** Projects can be created with a past deadline or with no skills, which then break matching/recommendations downstream.
- **Fix:** Validate `deadline > now` and require at least one skill at creation.
- **Expected outcome:** Malformed projects are rejected at creation with a clear 400.

### L13 — Unvalidated int/date query params → 500 in bidding
- **Location:** `apps/bidding/views/views.py:126`
- **Bug:** Query params are cast to int/date without validation, so malformed input raises instead of returning a 400.
- **Fix:** Validate/parse params defensively (serializer or try/except → 400).
- **Expected outcome:** Bad query params return 400, not 500.

### L14 — `services_digest` references `timezone` without importing it
- **Location:** `apps/notifications/services/services_digest.py:10`
- **Bug:** Uses `timezone` with no import → `NameError` if the code path runs. (Part of the dead "extended" layer below.)
- **Fix:** `from django.utils import timezone` and verify the field names it uses actually exist.
- **Expected outcome:** The digest path runs without a `NameError`.

---

## Cross-cutting theme — a dead "extended" service layer

A whole secondary layer of `*_extended` / `services_*` files reference **model fields that don't exist**, so those features are guaranteed to 500 or are silently dead. These are the biggest remaining source of latent 500s after the items above.

- **bidding:** `services_counter_offer.py:48`,`:90`,`:95`,`:132` (wrong fields, missing `expires_at`, undefined `timezone`); `services_retraction.py:52` (`Bid.Status.RETRACTED` doesn't exist — only `PENDING/ACCEPTED/REJECTED/WITHDRAWN`); `services_worklog_approval.py:47`,`:153` (`approved_by` should be `client`); `serializers_extended.py:127` (`CounterOfferResponseSerializer` non-existent fields); `services_termination.py:141`,`:272` (`termination_reason` non-existent field).
- **notifications:** `services_announcement.py:11`, `services_digest.py:10` (+ `timezone` NameError, see L14).
- **messaging:** `services_search.py:11`.
- **search:** covered by H9 (`required_skills`, `frequency`) and M12 (`draft_data`).

**Fix (general):** For each file, reconcile every field reference against the actual model, add missing enum members via migration where genuinely needed (e.g. a `RETRACTED` bid status), fix imports, and add a test that exercises the endpoint. If a feature isn't shipping, delete the file rather than leaving a 500 trap.
**Expected outcome:** Every registered endpoint either works against the real schema or is removed — no endpoints that 500 the moment they're called.

---

## Issue.md mapping

| # | Reported in `Issue.md` | Root cause (this report) |
|---|------------------------|--------------------------|
| 1 | No suggestions on client dashboard | H7 + H8 + H9 (skill matching AND-chained/case-sensitive, ES keyword, `required_skills`/`frequency` FieldErrors) |
| 2 | Integrate email system both sides | H1 (email verification 500s every call; `is_active=True` default gates nothing) |
| 6 | Stuck in profile image uploading | M3 (double upload + no axios timeout) |
| 7 | Signed in without account → redirected as freelancer | H2 (login defaults role to FREELANCER) |
| 8 | Stuck redirecting on the login page | C3 (route redirect loop) + H3 (Google callback error path) |
| 11 | Read receipts | M4 (marked read on delivery, not viewing) |
| 14 | Show the commission we deduct | M1 (earnings reported gross; platform cut never surfaced) |

---

## Confirmed NOT bugs (false positives avoided)

- **Milestone equal-distribution is correct** — Decimal math, `ROUND_DOWN`, the last milestone absorbs the remainder, and `milestone_count < 1` is rejected.
- **`.env` is not committed** — it's gitignored and `git ls-files` confirms it's untracked; no secrets-in-repo.
- **Freelancer payout money math is safe** — the payout task uses `int(Decimal(str(amount)) * 100)`; only the *refund* path has the paise defect (L3).
- **`core/cache.py` crash is latent, not live** — the module has no callers (L4).
- **`services_milestone.py` `except Exception: pass` blocks are benign** — they wrap only a post-commit WebSocket broadcast (which already catches internally); no money/state is hidden.
