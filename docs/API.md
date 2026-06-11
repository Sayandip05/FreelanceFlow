# FreelanceFlow — API Reference

**Base URL:** `https://api.freelanceflow.com`  
**Version:** 1.0  
**Auth:** JWT Bearer token (all endpoints except `register`, `login`, `token/refresh`, `webhook`)  
**Content-Type:** `application/json` (unless noted as multipart)

---

## Table of Contents

1. [Authentication Conventions](#1-authentication-conventions)
2. [Standard Response Shapes](#2-standard-response-shapes)
3. [Rate Limiting & Throttling](#3-rate-limiting--throttling)
4. [Users & Auth](#4-users--auth)
5. [Two-Factor Authentication (2FA)](#5-two-factor-authentication-2fa)
6. [Activity Log & Online Status](#6-activity-log--online-status)
7. [Projects](#7-projects)
8. [Bidding](#8-bidding)
9. [Contracts](#9-contracts)
10. [Counter-Offers](#10-counter-offers)
11. [Worklog Approvals](#11-worklog-approvals)
12. [Reviews](#12-reviews)
13. [Payments (Escrow)](#13-payments-escrow)
14. [Payment Milestones](#14-payment-milestones)
15. [Work Logs](#15-work-logs)
16. [Deliverables](#16-deliverables)
17. [AI Chat (Work Report Generator)](#17-ai-chat-work-report-generator)
18. [Weekly Reports](#18-weekly-reports)
19. [Delivery Proofs](#19-delivery-proofs)
20. [File Upload](#20-file-upload)
21. [Messaging (REST)](#21-messaging-rest)
22. [WebSocket — Real-Time Chat](#22-websocket--real-time-chat)
23. [Notifications](#23-notifications)
24. [Search](#24-search)
25. [Developer Tools (Local Only)](#25-developer-tools-local-only)
26. [Error Codes Reference](#26-error-codes-reference)

---

## 1. Authentication Conventions

All protected endpoints require:

```http
Authorization: Bearer <access_token>
```

**Token Lifetimes:**
- Access token: **60 minutes**
- Refresh token: **7 days** (rotates on every use — old token blacklisted)

**Auth endpoints** (`register`, `login`, `token/refresh`) are **public** — no token needed.  
**Webhook** (`POST /api/payments/webhook/`) uses Razorpay HMAC signature instead of JWT.

---

## 2. Standard Response Shapes

### Success — List (paginated)

```json
{
  "count": 42,
  "next": "https://api.freelanceflow.com/api/projects/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

### Success — Single Object

```json
{ "id": 1, "field": "value", ... }
```

### Success — Action

```json
{ "message": "Human-readable confirmation." }
```

### Error

```json
{
  "error": "Human-readable message.",
  "code": "machine_readable_code",
  "field": "field_name_if_applicable"
}
```

### Validation Error (DRF default)

```json
{
  "field_name": ["Error message."]
}
```

---

## 3. Rate Limiting & Throttling

| Scope | Limit |
|---|---|
| **Anonymous** (unauthenticated) | `100 / hour` |
| **Authenticated users** | `1000 / hour` |
| **Auth endpoints** (register, login, change-password) | `5 / minute` (custom `AuthRateThrottle`) |

Exceeded limit → `HTTP 429 Too Many Requests`

---

## 4. Users & Auth

### Base path: `/api/users/`

---

#### `POST /api/users/register/`

Register a new user account.  
**Auth:** Public · **Throttle:** 5/min

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "FREELANCER"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string | ✅ | Must be unique |
| `password` | string | ✅ | Django password validators apply |
| `first_name` | string | ✅ | |
| `last_name` | string | ✅ | |
| `role` | enum | ✅ | `CLIENT` or `FREELANCER` |

**Response `201`:**
```json
{
  "message": "User registered successfully.",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "FREELANCER"
  }
}
```

---

#### `POST /api/users/login/`

Login and receive JWT token pair.  
**Auth:** Public · **Throttle:** 5/min · **Brute-force:** locked after 5 failures (5-min window)

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response `200`:**
```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

**Errors:**
- `401` — Invalid credentials
- `429` — Rate limit / brute-force lockout

---

#### `POST /api/users/token/refresh/`

Rotate JWT token pair.  
**Auth:** Public (uses refresh token, not access token)

**Request:**
```json
{ "refresh": "<refresh_token>" }
```

**Response `200`:**
```json
{
  "access": "<new_access_token>",
  "refresh": "<new_refresh_token>"
}
```
> Old refresh token is **blacklisted** after this call.

---

#### `GET /api/users/me/`

Get current user's full profile.  
**Auth:** Required

**Response `200`:**
```json
{
  "id": 1,
  "email": "jane@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "FREELANCER",
  "is_deactivated": false,
  "freelancer_profile": {
    "bio": "Full-stack developer",
    "skills": ["Python", "React"],
    "hourly_rate": "75.00",
    "subscription_tier": "FREE",
    "total_earned": "4500.00",
    "avatar": "https://...",
    "is_available": true,
    "average_rating": "4.80",
    "total_reviews": 12
  }
}
```
> `freelancer_profile` or `client_profile` is present based on role.

---

#### `PATCH /api/users/me/`

Update current user's profile.  
**Auth:** Required

**Request:** (all fields optional)
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "bio": "Updated bio",
  "skills": ["Python", "Django", "React"],
  "hourly_rate": "85.00"
}
```

---

#### `GET /api/users/<int:pk>/`

Get public profile of any user by ID.  
**Auth:** Required

---

#### `POST /api/users/change-password/`

Change password for authenticated user.  
**Auth:** Required · **Throttle:** 5/min

**Request:**
```json
{
  "old_password": "current_password",
  "new_password": "NewSecurePass123!"
}
```

**Response `200`:**
```json
{ "message": "Password changed successfully." }
```

---

#### `POST /api/users/avatar/`

Upload or update profile avatar URL.  
**Auth:** Required

**Request:**
```json
{ "avatar": "https://cdn.example.com/avatars/user-1.jpg" }
```

---

#### `POST /api/users/availability/`

Toggle freelancer availability status.  
**Auth:** Required (Freelancer only)

**Response `200`:**
```json
{
  "message": "Availability updated.",
  "is_available": false
}
```

---

#### `POST /api/users/password-reset/`

Request password reset email.  
**Auth:** Public

**Request:**
```json
{ "email": "user@example.com" }
```

**Response `200`:**
```json
{ "message": "Password reset email sent if account exists." }
```

---

#### `POST /api/users/password-reset/confirm/`

Confirm password reset with token from email.  
**Auth:** Public

**Request:**
```json
{
  "uid": "<uid_from_email>",
  "token": "<token_from_email>",
  "new_password": "NewPass123!"
}
```

---

#### `POST /api/users/verify-email/`

Verify email address with token from email.  
**Auth:** Public

**Request:**
```json
{ "token": "<verification_token>" }
```

---

#### `POST /api/users/resend-verification/`

Resend email verification link.  
**Auth:** Public

**Request:**
```json
{ "email": "user@example.com" }
```

---

#### `POST /api/users/deactivate/`

Soft-delete (deactivate) current user account.  
**Auth:** Required

**Request:**
```json
{ "password": "confirm_with_password" }
```

**Response `200`:**
```json
{ "message": "Account deactivated. Data retained for 30 days." }
```

---

#### `POST /api/users/reactivate/`

Reactivate a deactivated account.  
**Auth:** Public (user can't be logged in)

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

---

## 5. Two-Factor Authentication (2FA)

### Base path: `/api/users/2fa/`

All endpoints require authentication.  
Uses TOTP (Time-based One-Time Password) compatible with Google Authenticator, Authy, etc.

---

#### `POST /api/users/2fa/enable/`

Generate 2FA secret and QR code URI. 2FA is **not yet active** until verified.

**Response `200`:**
```json
{
  "secret_key": "JBSWY3DPEHPK3PXP",
  "backup_codes": ["A1B2", "C3D4", "E5F6", "G7H8", "I9J0", "K1L2", "M3N4", "O5P6", "Q7R8", "S9T0"],
  "qr_code_url": "otpauth://totp/FreelanceFlow:jane@example.com?secret=JBSWY3DPEHPK3PXP&issuer=FreelanceFlow"
}
```

---

#### `POST /api/users/2fa/verify/`

Verify TOTP code from authenticator app and **activate** 2FA.

**Request:**
```json
{ "code": "123456" }
```

**Response `200`:**
```json
{ "message": "2FA enabled successfully", "enabled": true }
```

**Response `400`:** Invalid code — 2FA stays inactive.

---

#### `POST /api/users/2fa/disable/`

Disable 2FA (requires current valid TOTP or backup code).

**Request:**
```json
{ "code": "123456" }
```

**Response `200`:**
```json
{ "message": "2FA disabled successfully", "enabled": false }
```

---

#### `GET /api/users/2fa/status/`

Check whether 2FA is currently enabled.

**Response `200`:**
```json
{ "enabled": true }
```

---

#### `POST /api/users/2fa/regenerate-codes/`

Replace all remaining backup codes with 10 new ones.  
Requires 2FA to already be enabled.

**Response `200`:**
```json
{
  "backup_codes": ["AA11", "BB22", ...],
  "message": "Backup codes regenerated successfully"
}
```

---

## 6. Activity Log & Online Status

### Activity Log — `/api/users/activity/`

**Auth:** Required (own logs only)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/users/activity/` | List last 100 activity events |
| `GET` | `/api/users/activity/security/` | Security events only (login, pw change) — last 50 |
| `GET` | `/api/users/activity/summary/?days=30` | Aggregated counts by action type |

**Activity event types:** `LOGIN`, `LOGOUT`, `PROJECT_CREATED`, `BID_PLACED`, `CONTRACT_SIGNED`, `PAYMENT_MADE`, `REVIEW_POSTED`, `PROFILE_UPDATED`, `PASSWORD_CHANGED`, `OTHER`

**Sample response — list item:**
```json
{
  "id": 1,
  "action_type": "LOGIN",
  "description": "User logged in",
  "ip_address": "192.168.1.1",
  "created_at": "2026-06-11T08:00:00Z"
}
```

**Sample response — summary:**
```json
[
  { "action": "LOGIN", "count": 15 },
  { "action": "BID_PLACED", "count": 3 }
]
```

---

### Online Status — `/api/users/status/`

**Auth:** Required

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/users/status/me/` | Get my online status |
| `POST` | `/api/users/status/message/` | Set status message |
| `DELETE` | `/api/users/status/message/` | Clear status message |
| `GET` | `/api/users/status/online/?limit=50` | List currently online users |
| `GET` | `/api/users/status/count/` | Count of online users |

**`GET /api/users/status/me/` response:**
```json
{
  "is_online": true,
  "last_seen": "2026-06-11T12:00:00Z"
}
```

**`GET /api/users/status/count/` response:**
```json
{ "online_count": 42 }
```

---

## 7. Projects

### Base path: `/api/projects/`

**Auth:** Required for all endpoints.

---

#### `GET /api/projects/`

List projects. Clients see their own. Freelancers see open projects.

**Query params:**

| Param | Type | Description |
|---|---|---|
| `status` | string | `OPEN`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `DRAFT` |
| `search` | string | Full-text filter on title/description |
| `ordering` | string | `-created_at`, `budget`, `-budget`, `deadline` |
| `min_budget` | decimal | Minimum budget filter |
| `max_budget` | decimal | Maximum budget filter |

**Response `200`:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Build Django REST API",
      "description": "...",
      "budget": "5000.00",
      "deadline": "2026-07-01",
      "status": "OPEN",
      "client": { "id": 2, "email": "client@example.com", "full_name": "John Client" },
      "skills": ["Python", "Django", "PostgreSQL"],
      "bid_count": 3,
      "created_at": "2026-06-01T10:00:00Z"
    }
  ]
}
```

---

#### `POST /api/projects/`

Create a new project.  
**Permission:** Client only

**Request:**
```json
{
  "title": "Build Django REST API",
  "description": "Need a senior developer to build a full REST API with JWT auth...",
  "budget": "5000.00",
  "deadline": "2026-07-01",
  "skills": ["Python", "Django", "PostgreSQL"],
  "category": 3
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | ✅ | |
| `description` | string | ✅ | |
| `budget` | decimal | ✅ | |
| `deadline` | date | ❌ | ISO 8601 `YYYY-MM-DD` |
| `skills` | list[string] | ❌ | |
| `category` | int (FK) | ❌ | `ProjectCategory` ID |

**Response `201`:** Full project object.

---

#### `GET /api/projects/<id>/`

Get full project detail.

---

#### `PATCH /api/projects/<id>/`

Update project.  
**Permission:** Project owner (client) only

---

#### `DELETE /api/projects/<id>/`

Delete project.  
**Permission:** Project owner only. Only allowed when `status = DRAFT`.

---

#### `POST /api/projects/<id>/publish/`

Publish draft project — changes status `DRAFT → OPEN`.  
**Permission:** Project owner only

**Response `200`:**
```json
{ "message": "Project published.", "status": "OPEN" }
```

---

#### `POST /api/projects/<id>/cancel/`

Cancel an open or in-progress project.  
**Permission:** Project owner only

**Request:**
```json
{ "reason": "Client budget changed" }
```

---

#### `GET /api/projects/bookmarks/`

List bookmarked projects for current user.

---

#### `POST /api/projects/bookmarks/`

Bookmark a project.

**Request:**
```json
{
  "project": 5,
  "notes": "Good budget, match my skills"
}
```

---

#### `DELETE /api/projects/bookmarks/<id>/`

Remove a bookmark.

---

## 8. Bidding

### Base path: `/api/bidding/bids/`

---

#### `GET /api/bidding/bids/`

- **Freelancer:** returns their own submitted bids
- **Client:** returns all bids on their projects

---

#### `POST /api/bidding/bids/`

Submit a bid on a project.  
**Permission:** Freelancer only

**Request:**
```json
{
  "project": 5,
  "amount": "4500.00",
  "cover_letter": "I am a senior Django developer with 5 years of experience building REST APIs..."
}
```

| Field | Type | Required | Validation |
|---|---|---|---|
| `project` | int | ✅ | Must be `OPEN`, freelancer must not have bid already |
| `amount` | decimal | ✅ | Must be > 0 and ≤ project budget |
| `cover_letter` | string | ✅ | Minimum 50 characters |

**Response `201`:**
```json
{
  "id": 10,
  "project": { "id": 5, "title": "Build Django REST API" },
  "amount": "4500.00",
  "cover_letter": "...",
  "status": "PENDING",
  "created_at": "2026-06-11T10:00:00Z"
}
```

**Errors:**
- `400` `already_bid` — Freelancer already bid on this project
- `400` `amount_exceeds_budget` — Bid exceeds project budget
- `400` `cover_letter_too_short` — Under 50 characters
- `400` `project_not_open` — Project is not accepting bids

---

#### `GET /api/bidding/bids/<id>/`

Get bid detail.

---

#### `DELETE /api/bidding/bids/<id>/`

Withdraw a bid (sets status to `WITHDRAWN`).  
**Permission:** Bid owner (freelancer) only  
**Constraint:** Only `PENDING` bids can be withdrawn.

**Response `200`:**
```json
{ "message": "Bid withdrawn successfully." }
```

---

#### `POST /api/bidding/bids/<id>/accept/`

Accept a bid — creates a `Contract` automatically, rejects all other pending bids.  
**Permission:** Project owner (client) only  
Uses `SELECT FOR UPDATE` to prevent race conditions.

**Response `201`:**
```json
{
  "message": "Bid accepted successfully.",
  "contract": {
    "id": 7,
    "agreed_amount": "4500.00",
    "start_date": "2026-06-11T10:05:00Z",
    "is_active": true
  }
}
```

---

#### `POST /api/bidding/bids/<id>/reject/`

Reject a specific bid.  
**Permission:** Project owner (client) only

**Response `200`:**
```json
{ "message": "Bid rejected successfully." }
```

---

#### `GET /api/bidding/bids/my_bids/`

Shortcut — list current freelancer's bids only.  
**Permission:** Freelancer only

---

## 9. Contracts

### Base path: `/api/bidding/contracts/`

**Auth:** Required. Returns only contracts the user is a party to (client or freelancer).

---

#### `GET /api/bidding/contracts/`

List user's contracts.

**Response item:**
```json
{
  "id": 7,
  "bid": { "id": 10, "amount": "4500.00" },
  "agreed_amount": "4500.00",
  "start_date": "2026-06-11",
  "end_date": null,
  "is_active": true,
  "project": { "id": 5, "title": "Build Django REST API" },
  "client": { "id": 2, "email": "client@example.com" },
  "freelancer": { "id": 3, "email": "jane@example.com" }
}
```

---

#### `GET /api/bidding/contracts/<id>/`

Get full contract detail.

---

## 10. Counter-Offers

### Base path: `/api/bidding/counter-offers/`

Clients can make counter-offers on bids before accepting.

---

#### `POST /api/bidding/counter-offers/<bid_id>/counter-offer/`

Create a counter-offer on a bid.  
**Permission:** Project client only

**Request:**
```json
{
  "counter_amount": "4200.00",
  "counter_timeline": "2026-07-15",
  "message": "Happy to work with you but budget is slightly tight..."
}
```

**Response `201`:**
```json
{
  "message": "Counter-offer created successfully",
  "counter_offer": {
    "id": 3,
    "counter_amount": "4200.00",
    "counter_timeline": "2026-07-15",
    "message": "...",
    "status": "PENDING"
  }
}
```

---

#### `POST /api/bidding/counter-offers/<id>/accept/`

Accept a counter-offer (freelancer accepts the new terms).  
**Permission:** Bid owner (freelancer)

**Response `200`:**
```json
{ "message": "Counter-offer accepted", "bid": { ... } }
```

---

#### `POST /api/bidding/counter-offers/<id>/reject/`

Reject a counter-offer.

**Request:**
```json
{ "reason": "Cannot lower my rate for this scope" }
```

---

#### `GET /api/bidding/counter-offers/<bid_id>/counter-offers/`

List all counter-offers for a bid.

---

#### `GET /api/bidding/counter-offers/pending/`

Pending counter-offers for current freelancer.

---

#### `GET /api/bidding/counter-offers/stats/`

Counter-offer acceptance rate statistics for current user.

**Response:**
```json
{
  "total_sent": 10,
  "accepted": 6,
  "rejected": 2,
  "pending": 2,
  "acceptance_rate": 0.75
}
```

---

## 11. Worklog Approvals

### Base path: `/api/bidding/worklog-approvals/`

Alternative approval flow (separate from the direct worklog approve/reject in §15).

---

#### `POST /api/bidding/worklog-approvals/<worklog_id>/submit-approval/`

Submit a worklog for formal client approval.  
**Permission:** Freelancer on the contract

---

#### `POST /api/bidding/worklog-approvals/<id>/approve/`

Approve a worklog.  
**Permission:** Client on the contract

**Request:**
```json
{ "feedback": "Great work, looks exactly like what we discussed." }
```

---

#### `POST /api/bidding/worklog-approvals/<id>/reject/`

Reject a worklog.

**Request:**
```json
{ "feedback": "The API endpoint for user auth is missing." }
```

---

#### `GET /api/bidding/worklog-approvals/pending/`

List pending worklog approvals for current client (up to 50).

---

#### `GET /api/bidding/worklog-approvals/<worklog_id>/approval-status/`

Get the current approval status for a specific worklog.

---

### Bid Retraction — `/api/bidding/retractions/`

---

#### `POST /api/bidding/retractions/<bid_id>/retract/`

Formally retract a bid (different from `DELETE` withdraw — preserves retraction record).

**Request:**
```json
{ "reason": "Found another project" }
```

---

#### `GET /api/bidding/retractions/<bid_id>/can-retract/`

Check if a bid can be retracted.

**Response:**
```json
{ "can_retract": true, "reason": null }
```

---

#### `GET /api/bidding/retractions/`

List current user's retracted bids.

---

## 12. Reviews

### Base path: `/api/bidding/reviews/`

> **Note:** Review model exists in `apps.bidding` (`models_review.py`). The `ReviewViewSet` is registered. Full review submission API is implemented via `services_review.py`.

---

#### `GET /api/bidding/reviews/`

List reviews relevant to current user.

---

#### `POST /api/bidding/reviews/`

Submit a review for a completed contract.  
**Permission:** Contract participant (either party)

**Request:**
```json
{
  "contract": 7,
  "rating": 5,
  "comment": "Excellent freelancer, delivered on time and above expectations."
}
```

---

#### `GET /api/bidding/reviews/<id>/`

Get review detail.

---

## 13. Payments (Escrow)

### Base path: `/api/payments/`

---

#### `GET /api/payments/`

List payments for current user.
- **Client:** payments where they are the payer
- **Freelancer:** payments where they are the recipient

**Response item:**
```json
{
  "id": 1,
  "contract": 7,
  "total_amount": "4500.00",
  "status": "ESCROWED",
  "razorpay_order_id": "order_xxx",
  "created_at": "2026-06-11T10:00:00Z"
}
```

**Payment statuses:** `PENDING` → `ESCROWED` → `PAYOUT_PENDING` → `RELEASED` or `PAYOUT_FAILED` or `REFUNDED`

---

#### `GET /api/payments/<id>/`

Get payment detail.

---

#### `POST /api/payments/escrow/`

Create escrow payment (Razorpay order) for a contract.  
**Permission:** Contract client only

**Request:**
```json
{ "contract_id": 7 }
```

**Response `201`:**
```json
{
  "message": "Escrow created successfully.",
  "payment": { "id": 1, "status": "PENDING", ... },
  "razorpay_order_id": "order_NF0Xxxxxxxx",
  "amount": 450000,
  "currency": "INR"
}
```
> `amount` is in **paise** (multiply ₹ by 100). Pass directly to Razorpay checkout.

**Next step:** Use `razorpay_order_id` + `amount` + `currency` to open the Razorpay Checkout modal on the frontend.

---

#### `POST /api/payments/verify/`

Verify payment after user completes Razorpay checkout.  
**Auth:** Required (the paying client)  
Called immediately after `razorpay.payment.success` callback from checkout.

**Request:**
```json
{
  "razorpay_order_id": "order_NF0Xxxxxxxx",
  "razorpay_payment_id": "pay_NF1Xxxxxxxx",
  "razorpay_signature": "<hmac_sha256_signature>"
}
```

**Response `200`:**
```json
{
  "message": "Payment verified successfully.",
  "payment": { "id": 1, "status": "ESCROWED", ... }
}
```

**Errors:**
- `400` `invalid_signature` — HMAC verification failed
- `400` `missing_data` — One or more fields missing

---

#### `POST /api/payments/release/`

Release escrowed funds to freelancer.  
**Permission:** Contract client only  
Triggers RazorpayX IMPS payout asynchronously via Celery.

**Request:**
```json
{ "contract_id": 7 }
```

**Response `200`:**
```json
{
  "message": "Payment release initiated successfully.",
  "payment": { "id": 1, "status": "PAYOUT_PENDING", ... }
}
```

---

#### `GET /api/payments/history/`

Summary of payment activity for current user.

**Response:**
```json
{
  "total_spent": "9000.00",
  "total_earned": "0.00",
  "pending_escrow": "4500.00"
}
```
> For clients: `total_spent` and `pending_escrow` populated.  
> For freelancers: `total_earned` populated.

---

#### `POST /api/payments/webhook/`

Razorpay webhook receiver.  
**Auth:** None (uses `X-Razorpay-Signature` HMAC verification internally)  
**Content-Type:** `application/json`

**Headers required by Razorpay:**
```
X-Razorpay-Signature: <hmac_sha256>
X-Razorpay-Event-Id: <unique_event_id>
```

**Behavior:**
| Scenario | HTTP Response |
|---|---|
| Valid signature, new event | `200 {"status": "success"}` |
| Invalid signature | `200 {"status": "ignored", "reason": "invalid_signature"}` |
| Missing event ID | `400` — Razorpay will retry |
| Already processed event | `200` (idempotent) |
| Internal error | `200` — prevents infinite retry loop |

**Handled events:**
- `payment.captured` → confirms escrow (`PENDING → ESCROWED`)
- `payment.failed` → logs failure event

---

## 14. Payment Milestones

### Base path: `/api/payments/milestones/`

Break a contract payment into sequential milestone payments.

---

#### `POST /api/payments/milestones/<contract_id>/milestones/`

Create a milestone for a contract.  
**Permission:** Contract client

**Request:**
```json
{
  "title": "Frontend UI Complete",
  "description": "All React components built and tested",
  "amount": "1500.00",
  "due_date": "2026-06-25"
}
```

| Validation | Rule |
|---|---|
| `amount` | Must be > 0 |
| Total milestones | Must not exceed `contract.agreed_amount` |
| `percentage` | Auto-calculated as `(amount / agreed_amount) × 100` |

**Response `201`:**
```json
{
  "message": "Milestone created successfully",
  "milestone": {
    "id": 1,
    "title": "Frontend UI Complete",
    "amount": "1500.00",
    "percentage": "33.33",
    "order": 1,
    "status": "PENDING",
    "due_date": "2026-06-25"
  }
}
```

---

#### `GET /api/payments/milestones/<contract_id>/milestones/`

List all milestones for a contract.

---

#### `POST /api/payments/milestones/<milestone_id>/complete/`

Mark milestone as completed — submitted for client review.  
**Permission:** Contract freelancer only  
Changes status `PENDING → SUBMITTED`.

**Response `200`:**
```json
{
  "message": "Milestone marked as completed",
  "milestone": { "id": 1, "status": "SUBMITTED", "submitted_at": "2026-06-20T15:00:00Z" }
}
```

---

#### `POST /api/payments/milestones/<milestone_id>/release/`

Approve and release payment for a milestone.  
**Permission:** Contract client only  
Changes status `SUBMITTED/APPROVED → APPROVED` then triggers payout.

**Response `200`:**
```json
{
  "message": "Milestone payment release initiated",
  "payment": { "id": 1, "status": "PAYOUT_PENDING" }
}
```

---

#### `GET /api/payments/milestones/<contract_id>/milestone-progress/`

Aggregated milestone progress for a contract.

**Response:**
```json
{
  "total_amount": "4500.00",
  "total_count": 3,
  "completed_count": 1,
  "paid_count": 1,
  "paid_amount": "1500.00"
}
```

---

#### `GET /api/payments/milestones/upcoming/?days=30&limit=10`

Upcoming milestones for current user.

| Param | Default | Description |
|---|---|---|
| `days` | `30` | Look-ahead window |
| `limit` | `10` | Max results |

---

## 15. Work Logs

### Base path: `/api/worklogs/logs/`

Daily work logs submitted by freelancers.  
**Constraint:** One log per contract per calendar day.

---

#### `GET /api/worklogs/logs/?contract=<id>`

List work logs.  
- Freelancers: their own logs (optionally filtered by contract)
- Clients: logs on their contracts

**Query params:**

| Param | Description |
|---|---|
| `contract` | Filter by contract ID |

---

#### `POST /api/worklogs/logs/?contract=<contract_id>`

Create a daily work log.  
**Permission:** Freelancer on the contract  
**Content-Type:** `application/json`

**Request:**
```json
{
  "date": "2026-06-11",
  "description": "Implemented JWT authentication with refresh token rotation",
  "hours_worked": "7.5",
  "screenshot_url": "https://cdn.example.com/screens/work.png",
  "reference_url": "https://github.com/myrepo/pull/42"
}
```

| Field | Type | Required | Validation |
|---|---|---|---|
| `date` | date | ✅ | ISO 8601. Must be unique per contract. |
| `description` | string | ✅ | |
| `hours_worked` | decimal | ✅ | 0.1–24.0 |
| `screenshot_url` | string | ❌ | URL to existing screenshot |
| `reference_url` | string | ❌ | GitHub, Figma, Jira URL etc. |

**Response `201`:** Full WorkLog object with `status: "DRAFT"`.

---

#### `GET /api/worklogs/logs/<id>/`

Get work log detail.

---

#### `PATCH /api/worklogs/logs/<id>/`

Update a work log.  
**Permission:** Log's freelancer only  
**Constraint:** Only `DRAFT` logs can be edited.

---

#### `DELETE /api/worklogs/logs/<id>/`

Delete a work log.  
**Permission:** Log's freelancer only  
**Constraint:** Only `DRAFT` logs can be deleted.

---

### Screenshot Upload (multipart)

Use the file upload endpoint (§20) to upload screenshots, then include the returned URL in the worklog.

---

## 16. Deliverables

### Base path: `/api/worklogs/deliverables/`

Formal work deliverables with full AI-chat audit trail.

**Status lifecycle:** `DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED / REJECTED / REVISION_REQUESTED`

---

#### `GET /api/worklogs/deliverables/`

List deliverables for the current user (by contract role).

---

#### `POST /api/worklogs/deliverables/`

Create a deliverable draft (typically called after AI chat generates a report).

**Request:**
```json
{
  "contract": 7,
  "title": "JWT Authentication Module",
  "description": "Implemented complete JWT auth with refresh rotation",
  "ai_chat_transcript": [...],
  "ai_generated_report": "The developer implemented JWT authentication...",
  "attached_files": ["https://s3.amazonaws.com/..."],
  "hours_logged": 7.5
}
```

**Response `201`:** Deliverable object with `status: "DRAFT"`.

---

#### `GET /api/worklogs/deliverables/<id>/`

Get deliverable detail including full `ai_chat_transcript`.

---

#### `PATCH /api/worklogs/deliverables/<id>/`

Update a draft deliverable.  
**Permission:** Deliverable's freelancer  
**Constraint:** Only `DRAFT` deliverables can be edited.

---

#### `POST /api/worklogs/deliverables/<id>/submit/`

Submit deliverable for client review.  
**Permission:** Deliverable's freelancer  
Changes status `DRAFT → SUBMITTED`.

**Response `200`:**
```json
{
  "message": "Deliverable submitted for review.",
  "deliverable": { "id": 3, "status": "SUBMITTED", "submitted_at": "2026-06-11T12:00:00Z" }
}
```

---

#### `POST /api/worklogs/deliverables/<id>/approve/`

Approve the deliverable.  
**Permission:** Contract client

**Request:** (optional)
```json
{ "client_feedback": "Excellent implementation, exactly what we needed!" }
```

**Response `200`:**
```json
{ "deliverable": { "id": 3, "status": "APPROVED", "reviewed_at": "..." } }
```

---

#### `POST /api/worklogs/deliverables/<id>/reject/`

Reject the deliverable.  
**Permission:** Contract client

**Request:**
```json
{
  "client_feedback": "The refresh token rotation is missing.",
  "revision_notes": "Please add token rotation logic per the spec."
}
```

---

#### `POST /api/worklogs/deliverables/<id>/request-revision/`

Request changes without fully rejecting.  
Changes status to `REVISION_REQUESTED`. Freelancer can re-submit.

**Request:**
```json
{ "revision_notes": "The UI spacing needs to match the Figma designs." }
```

---

## 17. AI Chat (Work Report Generator)

### Base path: `/api/worklogs/ai-chat/`

Multi-turn AI conversation that generates structured work reports.  
Uses **Groq Llama 3.3 70B** via **LangGraph** state machine.

---

#### `POST /api/worklogs/ai-chat/message/`

Send a message to the AI and receive a response.

**Request:**
```json
{
  "message": "Today I built the JWT authentication module with refresh token rotation.",
  "chat_history": [
    { "role": "user", "content": "Hi, I want to log my work." },
    { "role": "assistant", "content": "Great! What did you work on today?" }
  ],
  "contract_id": 7
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `message` | string | ✅ | Current user message |
| `chat_history` | list | ✅ | Previous turns (empty list for first message) |
| `contract_id` | int | ✅ | Scopes the AI to the project context |

**Response `200` — AI asking follow-up:**
```json
{
  "message": "Great! What libraries or frameworks did you use for the JWT implementation?",
  "report_ready": false,
  "report_data": null
}
```

**Response `200` — Report ready:**
```json
{
  "message": "I've generated your work report based on our conversation.",
  "report_ready": true,
  "report_data": {
    "title": "JWT Authentication Module",
    "description": "Implemented complete JWT auth system with access/refresh token pair...",
    "hours_worked": 7.5,
    "tasks_completed": [
      "JWT token generation",
      "Refresh token rotation",
      "Token blacklisting"
    ],
    "technologies_used": ["Django REST Framework", "SimpleJWT", "Redis"],
    "blockers": [],
    "next_steps": ["Add 2FA integration", "Write unit tests"]
  }
}
```

**Frontend flow:**
1. Keep sending messages until `report_ready: true`
2. Show the `report_data` to the user for review
3. Call `POST /api/worklogs/deliverables/` with the report data + full `chat_history`

---

#### `POST /api/worklogs/ai-chat/generate-deliverable/`

Skip the chat flow and generate a deliverable directly from existing report data.

**Request:**
```json
{
  "contract_id": 7,
  "report_data": { ... }
}
```

---

## 18. Weekly Reports

### Base path: `/api/worklogs/reports/`

AI-generated weekly summaries. Created automatically by Celery Beat every Sunday night.

---

#### `GET /api/worklogs/reports/`

List weekly reports for the current user's contracts.

**Response item:**
```json
{
  "id": 5,
  "contract": 7,
  "week_start": "2026-06-02",
  "week_end": "2026-06-08",
  "ai_summary": "This week the freelancer implemented JWT authentication and user profile management...",
  "pdf_url": "https://s3.amazonaws.com/...?X-Amz-Expires=604800",
  "total_hours": "35.50",
  "created_at": "2026-06-08T23:59:00Z"
}
```
> `pdf_url` is an S3 pre-signed URL valid for **7 days**.

---

#### `GET /api/worklogs/reports/<id>/`

Get a specific weekly report.

---

## 19. Delivery Proofs

### Base path: `/api/worklogs/proofs/`

Final immutable PDF generated when escrow is released. Documents the entire project.

---

#### `GET /api/worklogs/proofs/<contract_id>/`

Get delivery proof for a contract.

**Response `200`:**
```json
{
  "id": 1,
  "contract": 7,
  "pdf_url": "https://s3.amazonaws.com/.../delivery_proof.pdf?X-Amz-Expires=604800",
  "generated_at": "2026-06-11T15:30:00Z",
  "total_hours": "120.50",
  "total_logs_count": 22,
  "total_deliverables": 8,
  "approved_deliverables": 8,
  "report_id": "DPF-a3f8b2c1-..."
}
```
> `report_id` is a tamper-evident unique ID for the document.

---

#### `POST /api/worklogs/proofs/<contract_id>/`

Manually trigger delivery proof generation (normally happens automatically after payout).

---

## 20. File Upload

### Base path: `/api/worklogs/upload/`

**Content-Type:** `multipart/form-data`  
**Auth:** Required

---

#### `POST /api/worklogs/upload/`

Upload a file (screenshot, attachment, etc.) to S3.

**Request (multipart):**
```
file: <binary>
```

**Response `201`:**
```json
{
  "url": "https://s3.amazonaws.com/bucket/worklogs/screenshots/2026/06/11/file.png"
}
```
> Use the returned `url` in worklog `screenshot_url` or deliverable `attached_files`.

---

## 21. Messaging (REST)

### Base path: `/api/messaging/`

HTTP endpoints for message history. For real-time messaging, use the WebSocket connection (§22).

---

#### `GET /api/messaging/conversations/`

List conversations for current user (one per contract).

**Response item:**
```json
{
  "id": 3,
  "contract": {
    "id": 7,
    "project_title": "Build Django REST API"
  },
  "last_message": {
    "content": "The PR is ready for review.",
    "sender": "jane@example.com",
    "created_at": "2026-06-11T11:30:00Z"
  },
  "unread_count": 2
}
```

---

#### `GET /api/messaging/conversations/<id>/`

Get conversation detail with message history.

---

#### `GET /api/messaging/messages/?conversation=<id>`

List messages in a conversation (paginated, newest first).

---

#### `POST /api/messaging/messages/`

Send a message (REST fallback — prefer WebSocket for real-time).

**Request:**
```json
{
  "conversation": 3,
  "content": "The PR is ready for your review.",
  "attachments": []
}
```

---

## 22. WebSocket — Real-Time Chat

**Protocol:** WSS (WebSocket Secure)  
**Auth:** JWT via query param (WebSocket headers not supported in browsers)

### Connection

```
wss://api.freelanceflow.com/ws/chat/<contract_id>/?token=<access_token>
```

| Param | Description |
|---|---|
| `contract_id` | Integer — the contract this chat belongs to |
| `token` | Valid JWT access token |

**On connect:** Server joins the client to Redis channel group `chat_{contract_id}` and loads message history.

---

### Message Format (Client → Server)

```json
{
  "type": "chat_message",
  "content": "The authentication module is complete.",
  "attachments": []
}
```

---

### Message Format (Server → Client)

```json
{
  "type": "chat_message",
  "id": 45,
  "content": "The authentication module is complete.",
  "sender": {
    "id": 3,
    "email": "jane@example.com",
    "full_name": "Jane Doe"
  },
  "attachments": [],
  "created_at": "2026-06-11T12:00:00Z"
}
```

---

### Typing Indicator (Client → Server)

```json
{ "type": "typing", "is_typing": true }
```

### Typing Indicator (Server → Client, broadcast)

```json
{
  "type": "typing",
  "user_id": 3,
  "is_typing": true
}
```

---

### Error (Server → Client)

```json
{
  "type": "error",
  "code": "unauthorized",
  "message": "Invalid or expired token."
}
```

---

### Disconnect

Server removes the client from the channel group. No explicit disconnect message needed.

---

## 23. Notifications

### Base path: `/api/notifications/notifications/`

**Auth:** Required (own notifications only)

---

#### `GET /api/notifications/notifications/`

List all notifications (paginated, newest first).

**Response item:**
```json
{
  "id": 10,
  "title": "Payment Released",
  "body": "Payment for Build Django REST API has been released.",
  "type": "PAYMENT_RELEASED",
  "is_read": false,
  "created_at": "2026-06-11T15:30:00Z"
}
```

**Notification types:** `BID_SUBMITTED`, `BID_ACCEPTED`, `ESCROW_CREATED`, `LOG_SUBMITTED`, `REPORT_READY`, `PAYMENT_RELEASED`, `PROOF_READY`, `MESSAGE_RECEIVED`

---

#### `GET /api/notifications/notifications/unread/`

Unread notifications only.

---

#### `GET /api/notifications/notifications/unread_count/`

```json
{ "unread_count": 5 }
```

---

#### `POST /api/notifications/notifications/<id>/mark_read/`

Mark a single notification as read.

**Response `200`:** Updated notification object.

---

#### `POST /api/notifications/notifications/mark_all_read/`

Mark all notifications as read.

**Response `200`:**
```json
{ "marked_as_read": 5 }
```

---

#### `DELETE /api/notifications/notifications/<id>/delete/`

Delete a notification.

**Response `204`:** No content.

---

## 24. Search

### Base path: `/api/search/`

Powered by **Elasticsearch 8**. Returns up to 50 results per query.

---

#### `GET /api/search/?q=<query>&type=<type>&skills=<skills>&min_budget=<n>&max_budget=<n>`

Unified search across projects and freelancers.

**Query params:**

| Param | Type | Default | Description |
|---|---|---|---|
| `q` | string | `""` | Full-text search query |
| `type` | enum | `all` | `projects`, `freelancers`, or `all` |
| `skills` | string | `""` | Comma-separated: `python,django,react` |
| `min_budget` | decimal | — | Projects only — minimum budget |
| `max_budget` | decimal | — | Projects only — maximum budget |

**ES scoring:** `title^3`, `description`, `skills` for projects; `full_name^2`, `bio`, `skills` for freelancers.

**Response:**
```json
{
  "projects": [
    {
      "id": 5,
      "title": "Build Django REST API",
      "description": "...",
      "budget": 5000,
      "status": "OPEN",
      "skills": ["Python", "Django"],
      "client_name": "John Client"
    }
  ],
  "freelancers": [
    {
      "id": 1,
      "full_name": "Jane Doe",
      "email": "jane@example.com",
      "bio": "Senior Django developer...",
      "skills": ["Python", "Django", "React"],
      "hourly_rate": 75
    }
  ]
}
```

---

#### `GET /api/search/projects/?q=<query>&skills=<skills>`

Projects-only search endpoint.

**Response:**
```json
{
  "results": [ ... ]
}
```

---

#### `GET /api/search/freelancers/?q=<query>&skills=<skills>`

Freelancers-only search endpoint.

**Response:**
```json
{
  "results": [ ... ]
}
```

---

## 25. Developer Tools (Local Only)

> **Production:** These routes are **never registered** when `DEBUG=False`. They have zero footprint in production.

Available when `DEBUG=True` (local development):

| URL | Description |
|---|---|
| `GET /api/schema/` | Raw OpenAPI 3.1 schema (JSON). Add `?format=yaml` for YAML. |
| `GET /api/docs/` | **Swagger UI** — interactive API explorer (equivalent to FastAPI's `/docs`) |
| `GET /api/redoc/` | **ReDoc** — alternative documentation UI (equivalent to FastAPI's `/redoc`) |
| `GET /` | Redirects to `/api/docs/` |

---

## 26. Error Codes Reference

### HTTP Status Codes

| Code | Meaning |
|---|---|
| `200` | OK |
| `201` | Created |
| `204` | No Content |
| `400` | Bad Request / Validation Error |
| `401` | Unauthorized (missing or expired token) |
| `403` | Forbidden (authenticated but no permission) |
| `404` | Not Found |
| `429` | Too Many Requests (throttle limit hit) |
| `500` | Internal Server Error |

### Application Error Codes

| `code` field | Meaning |
|---|---|
| `validation_error` | Input failed validation |
| `not_found` | Requested resource does not exist |
| `permission_denied` | User does not have the required role/permission |
| `already_bid` | Freelancer already bid on this project |
| `project_not_open` | Project is not accepting bids |
| `amount_exceeds_budget` | Bid amount exceeds project budget |
| `cover_letter_too_short` | Cover letter under 50 characters |
| `payment_exists` | Escrow already exists for this contract |
| `invalid_signature` | Razorpay HMAC verification failed |
| `invalid_data` | Request body missing required Razorpay fields |
| `escrow_required` | Payment must be in ESCROWED status |
| `not_escrowed` | Contract payment not yet funded |
| `2fa_not_enabled` | 2FA operation requires 2FA to be active |
| `invalid_2fa_code` | TOTP or backup code is incorrect |

---

*Document generated from live code scan — June 11, 2026*  
*All endpoints verified against URL configs, viewsets, and service layer.*
