# FreelanceFlow — Comprehensive Project Analysis

> **Author:** Sayandip Bar  
> **Repository:** [Sayandip05/FreelanceFlow](https://github.com/Sayandip05/FreelanceFlow)  
> **Analysis Date:** August 2026

---

## 1. What Is FreelanceFlow?

FreelanceFlow is an **AI-powered freelance marketplace backend** built on Django. It solves a core trust problem in freelancing:

- Clients pay upfront but get no delivery guarantee.
- Freelancers complete work but risk not getting paid.
- No transparent audit trail exists.

FreelanceFlow addresses this by combining **milestone-based escrow payments**, **AI-generated proof-of-work reports**, and **real-time WebSocket communication** to ensure complete accountability for both parties.

---

## 2. Tech Stack (At A Glance)

| Layer | Technology |
|---|---|
| **Framework** | Django 4.2 (Modular Monolith) |
| **API** | Django REST Framework (DRF) |
| **Database** | PostgreSQL (Supabase) / SQLite (local dev) |
| **Caching** | Redis 7 via `django-redis` |
| **Task Queue** | Celery + Celery Beat (`DatabaseScheduler`) |
| **WebSockets** | Django Channels + Daphne (ASGI) |
| **Search** | Elasticsearch 8.14 via `django-elasticsearch-dsl` |
| **Authentication** | SimpleJWT (60 min access / 7 day refresh) + Google OAuth2 SSO |
| **Brute Force Protection** | Django Axes (5 failures → 5-min lockout) |
| **AI / LLM** | Groq API (Llama 3.3 70B) + LangChain + LangGraph |
| **AI Monitoring** | LangSmith (`@traceable`) |
| **Payments** | Razorpay Escrow + RazorpayX Payouts |
| **PDF Generation** | WeasyPrint → bytes → Azure Blob Storage |
| **Cloud Storage** | Azure Blob Storage (SAS URLs, 7-day expiry) |
| **Monitoring** | Sentry (production), Flower (Celery UI) |
| **Frontend** | React 18 + Vite + TailwindCSS (separate) |
| **DevOps** | Docker Compose, Azure VM, Gunicorn + Daphne |

---

## 3. System Architecture

```
                          ┌─────────────────────────┐
                          │   React 18 + Vite UI    │  ← Port 5173
                          └────────────┬────────────┘
                                       │
                         HTTP/WS Proxy (Vite Gateway)
                                       │
              ┌────────────────────────┴────────────────────────┐
              │                                                 │
     ┌────────▼────────┐                               ┌────────▼────────┐
     │  Django WSGI    │                               │  Daphne ASGI    │
     │ (REST API :8000)│                               │  (WS :8001)     │
     └────────┬────────┘                               └────────┬────────┘
              │                                                 │
  ┌───────────┼──────────────┬────────────────────────────────┤
  │           │              │                                │
┌─▼──────┐  ┌─▼──────┐  ┌───▼──────┐                ┌───────▼──────┐
│  PG DB │  │ Redis  │  │  Celery  │                │Elasticsearch │
│(Supabase)│ │(Cache/ │  │Worker+  │                │  (Search)    │
│        │  │Broker/ │  │Beat     │                └──────────────┘
└────────┘  │Channels)│  └───┬──────┘
            └────────┘      │
                     ┌──────┴───────────┐
                     │                  │
              ┌──────▼──────┐  ┌────────▼────────┐
              │  Groq LLM   │  │  Azure Blob /   │
              │ (LangGraph) │  │  S3 Storage     │
              └─────────────┘  └─────────────────┘
```

**Redis serves 4 concurrent roles:**
1. **Cache** — Django's `CACHES` backend (prefix: `freelanceflow`)
2. **Celery Broker** — Task message queue (DB: 1)
3. **Celery Result Backend** — Task result storage (DB: 2)
4. **Channel Layer** — WebSocket group messaging (prefix: `freelanceflow:channels:`)

---

## 4. Project Directory Structure

```
FreelanceFlow/
├── apps/                      ← Business domain apps (8 apps)
│   ├── users/                 ← Auth, profiles, onboarding
│   ├── projects/              ← Job postings by clients
│   ├── bidding/               ← Bids + Contracts
│   ├── payments/              ← Razorpay escrow + payouts
│   ├── worklogs/              ← WorkLogs, AI reports, deliverables
│   ├── messaging/             ← Real-time chat (WebSocket)
│   ├── notifications/         ← In-app + email alerts
│   └── search/                ← Elasticsearch integration
│
├── config/                    ← Django project config
│   ├── settings/
│   │   ├── base.py            ← Core settings (installed apps, JWT, Redis, Celery, logging)
│   │   ├── local.py           ← Local/dev overrides
│   │   ├── production.py      ← Production hardening
│   │   └── test.py            ← Test-specific overrides
│   ├── asgi.py                ← ASGI entry (HTTP + WebSocket router)
│   ├── celery.py              ← Celery app, queues, task routing, graceful shutdown
│   ├── urls.py                ← Root URL dispatcher
│   ├── wsgi.py                ← WSGI entry
│   ├── gunicorn_config.py     ← Gunicorn production config
│   └── signals.py             ← Global signal handlers
│
├── core/                      ← Shared infrastructure
│   ├── cache.py               ← Redis cache wrappers
│   ├── decorators.py          ← Reusable decorators
│   ├── exceptions.py          ← Custom exception classes + DRF handler
│   ├── health.py              ← Health check endpoints
│   ├── management/            ← Custom Django management commands
│   ├── middleware.py          ← Request logging, security headers, rate limiting, CORS
│   ├── middleware_shutdown.py ← Graceful shutdown middleware
│   ├── pagination.py          ← Standard paginator (DRF)
│   ├── permissions.py         ← Shared DRF permission classes
│   ├── sanitizers.py          ← Input sanitization utilities
│   ├── throttles.py           ← Custom rate throttle classes
│   └── utils.py               ← General utilities (e.g., platform cut calculation)
│
├── deployment/                ← Infrastructure as Code
│   ├── cicd/                  ← CI/CD pipeline definitions
│   └── scripts/               ← Provisioning scripts
│
├── docs/                      ← Documentation
│   ├── API.md                 ← Full REST API reference
│   └── HLD.md                 ← High-level architecture design doc
│
├── scripts/
│   └── elasticsearch_setup.sh ← ES index initialization script
│
├── requirements/
│   ├── base.txt               ← Core dependencies
│   ├── local.txt              ← Dev-only extras
│   └── production.txt         ← Production extras
│
├── manage.py                  ← Django CLI entry point
├── conftest.py                ← pytest fixtures and setup
├── pytest.ini                 ← pytest configuration
├── docker-compose.yml         ← Multi-container Docker setup
├── Dockerfile                 ← Docker image for backend
├── Makefile                   ← Developer shortcut commands
└── .env / .env.example        ← Environment variables
```

---

## 5. How Each Domain App Works

### 5.1 `apps/users/` — Authentication & Profiles

**What it does:** Manages the entire user lifecycle — registration, login, JWT token management, Google OAuth, profile data, and account lifecycle.

**Key Files:**
- `models/models.py` — Three core models:
  - `User` — Custom user with **email as the primary identifier** (no username). Two roles: `CLIENT` and `FREELANCER`. Has soft-delete support (`is_deactivated`).
  - `FreelancerProfile` — Bio, skills (JSONField), hourly rate, avatar, city/country, `razorpay_fund_account_id`, subscription tier (FREE/PRO), onboarding status.
  - `ClientProfile` — Company info, industry, city/country, onboarding status.
- `models/models_extended.py` — Extended profile fields and verification document support.
- `services/services.py` — All business logic:
  - `create_user()` — Validates, creates User + auto-creates Profile (via signal)
  - `update_profile()` — Updates User + FreelancerProfile/ClientProfile atomically
  - `change_password()` / `send_password_reset_email()` / `reset_password()` — Full password lifecycle
  - `send_verification_email()` / `verify_email()` — Email verification with tokens
  - `deactivate_account()` / `reactivate_account()` — Soft-delete lifecycle
  - `toggle_freelancer_availability()` — Availability toggle
- `signals.py` — Auto-creates the appropriate profile when a User is first saved.
- `tasks.py` — Celery tasks (e.g., async email delivery).
- `tokens.py` — Custom token generators for password reset and email verification.

**Auth Flow:**
1. User registers → `create_user()` → signal creates profile → JWT tokens returned
2. Login via email/password → Django Axes checks brute force → JWT issued
3. Google OAuth → verify Google ID token → create/get user → JWT issued
4. Access token (60 min) + Refresh token (7 days, rotated, blacklisted on rotation)

---

### 5.2 `apps/projects/` — Job Listings

**What it does:** Manages projects posted by clients.

**Key Files:**
- `models/models.py` — `Project` (title, description, budget, deadline) with status machine: `OPEN → IN_PROGRESS → COMPLETED / CANCELLED`. `ProjectSkill` links skills to projects.
- `models/models_extended.py` — Extended project metadata (attachments, category tags, etc.)
- `services/` — Business logic for creating/updating projects, transitioning status.
- `selectors.py` — Reusable queryset helpers (e.g., `get_open_projects()`, `get_projects_for_client()`).
- `search` integration — Projects are indexed into Elasticsearch via `search/documents.py` and kept in sync via signals.

**Lifecycle:** A project starts as `OPEN`, transitions to `IN_PROGRESS` when a bid is accepted and a Contract is created, and moves to `COMPLETED` automatically when the final payment is released by the `razorpay_transfer_to_freelancer_task` Celery task.

---

### 5.3 `apps/bidding/` — Bids & Contracts

**What it does:** Manages the entire bidding process and contract creation.

**Key Files:**
- `models/models.py`:
  - `Bid` — A freelancer's proposal on a project. Contains `amount`, `cover_letter`, and a status machine: `PENDING → ACCEPTED / REJECTED / WITHDRAWN`. Enforces one bid per freelancer per project via `unique_together`.
  - `Contract` — Created when a Bid is accepted. Has `agreed_amount`, `start_date`, `is_active`. Exposes `project`, `freelancer`, `client` as properties via the `Bid` relation chain.
- `models/models_amendment.py` — Contract amendment requests (scope changes).
- `models/models_extended.py` — Extended contract fields, dispute tracking.
- `models/models_review.py` — Post-contract reviews.
- `models/models_termination.py` — Early contract termination logic.
- `services/` — `accept_bid()` creates a Contract atomically, rejects all other pending bids, changes project status to `IN_PROGRESS`.
- `selectors.py` — Queries like `get_bids_for_project()`, `get_active_contracts_for_user()`.
- `permissions.py` — Only the project owner (client) can accept/reject bids.

---

### 5.4 `apps/payments/` — Escrow & Payouts

**What it does:** The most critical and complex module. Handles the complete Razorpay escrow payment lifecycle.

**Key Files:**
- `models/` — `Payment`, `PlatformEarning`, `PaymentEvent` (idempotency lock), and `PaymentMilestone`.
- `services/services.py`:
  - `create_escrow_payment()` — Creates a Razorpay Order. Client pays into escrow.
  - `confirm_escrow_payment()` — Verifies HMAC-SHA256 signature to confirm authenticity.
  - `release_payment()` — Client triggers release from escrow → triggers the payout Celery task.
  - `process_refund()` — Issues a Razorpay refund.
  - `record_payment_event()` / `has_payment_event_been_processed()` — Idempotency layer using `PaymentEvent` unique constraint to prevent double-processing of webhook events.
- `tasks.py` — Three high-priority Celery tasks:
  - `process_razorpay_webhook_task` — Processes incoming Razorpay webhooks asynchronously (payment.captured, payment.failed). Checks idempotency before processing.
  - `razorpay_transfer_to_freelancer_task` — Executes the RazorpayX payout to the freelancer's registered fund account. On success: marks payment RELEASED, creates `PlatformEarning`, closes contract, marks project COMPLETED, marks milestones PAID, sends notification, triggers `generate_delivery_proof()`.
  - `process_razorpay_refund_task` — Processes refunds with 3 retries.
- `views/` — Webhook endpoint that verifies Razorpay signature header and dispatches to the task.

**Payment Flow:**
```
Client → POST /payments/create-escrow/
       → Razorpay Order created → Client pays in UI
       → Razorpay fires webhook → POST /payments/webhook/
       → Signature verified → process_razorpay_webhook_task.delay()
       → payment.captured event → confirm_escrow_payment()
       → Client → POST /payments/{id}/release/
       → razorpay_transfer_to_freelancer_task.delay()
       → RazorpayX Payout → Freelancer's bank account
       → Contract closed, Project COMPLETED, Delivery Proof generated
```

---

### 5.5 `apps/worklogs/` — Work Logs, AI Reports & Deliverables

**What it does:** The heart of the accountability system. Manages work tracking, AI-generated reports, and the entire deliverable review lifecycle.

**Key Models (`models/models.py`):**
- `WorkLog` — Daily log submitted by freelancer per contract. One per contract per day (`unique_together`). Has status: `DRAFT → PENDING_APPROVAL → APPROVED / REJECTED`. Stores hours, description, screenshots, AI summary from chat.
- `WeeklyReport` — AI-generated weekly/biweekly/monthly progress report. Stores the `ai_summary` (Markdown), `pdf_url` (Azure Blob SAS URL), and `interval_days`.
- `Deliverable` — A formal work submission with a 6-state lifecycle: `DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED / REJECTED / REVISION_REQUESTED`. Stores the full AI chat transcript as JSON, attached files, and client feedback.
- `DeliveryProof` — Final tamper-evident proof document generated at contract completion. One per contract.

**Key Model (`models/models_schedule.py`):**
- `ReportSchedule` — Client configures report cadence (7/14/30 days). Tracks `next_report_date`. Has `advance_to_next()` method called after each report is enqueued.

**AI Chat Flow (Deliverables):**
1. Freelancer calls `POST /api/worklogs/ai-chat/message/` with a text message.
2. The view is fully **async** (`sync_to_async`) to stay ASGI non-blocking.
3. The LangGraph `ChatAgentState` graph (Groq → Llama 3.3 70B) routes between asking follow-up questions and generating a structured JSON report.
4. Result stored as `Deliverable.ai_generated_report`.

**Automated Report Pipeline (Celery Beat):**
```
Celery Beat (00:05 daily)
  → trigger_scheduled_reports()
  → For each due ReportSchedule:
      → generate_ai_report_task.delay(contract_id, period_start, interval_days)
      → schedule.advance_to_next()

generate_ai_report_task
  → LangGraph 3-node pipeline: gather_logs → build_prompt → generate_report
  → WeeklyReport saved with ai_summary (Markdown)
  → generate_pdf_task.delay(report.id, 'weekly_report')
  → notify_freelancer_report_ready.delay(report.id)
  → notify_client_new_report.delay(report.id)

generate_pdf_task
  → WeasyPrint renders HTML → PDF bytes
  → Uploaded to Azure Blob Storage
  → 7-day SAS URL stored in WeeklyReport.pdf_url

Celery Beat (09:00 daily)
  → check_upcoming_report_deadlines()
  → Freelancers notified if report due in ≤ 3 days
```

---

### 5.6 `apps/messaging/` — Real-Time Chat

**What it does:** Provides contract-scoped real-time chat between client and freelancer over WebSockets.

**Key Files:**
- `consumers.py` — `ChatConsumer` (Async WebSocket Consumer):
  - **Authentication:** JWT passed as `?token=<access_token>` in the WebSocket URL query string. Validated via `rest_framework_simplejwt.tokens.AccessToken`.
  - **Authorization:** Only the contract's client and freelancer can connect. Checked via a single JOIN query using `select_related`.
  - **Connection:** Joins Redis channel group `chat_<contract_id>`.
  - **Messaging:** Validates → persists to DB → broadcasts to group via `group_send`.
  - **Read Receipts:** Auto-sends read receipt to group on connect and when receiving a message. Frontend sends `{"type": "read_receipt"}` to manually flush unread messages.
  - All ORM calls are wrapped in `database_sync_to_async` to prevent blocking the ASGI event loop.
- `routing.py` — Maps `ws://.../ws/chat/<contract_id>/` to `ChatConsumer`.
- `services/` — `send_message()`, `get_or_create_conversation()`, `mark_messages_as_read_returning_ids()`.
- `models/` — `Conversation` (linked to Contract), `Message` (content, sender, `is_read`, timestamp).

---

### 5.7 `apps/notifications/` — Notification System

**What it does:** In-app and email notification dispatch for all key events.

**Key Files:**
- `models/models.py` — `Notification` model with typed events: `BID_SUBMITTED`, `BID_ACCEPTED`, `ESCROW_CREATED`, `LOG_SUBMITTED`, `REPORT_READY`, `REPORT_UPCOMING`, `CLIENT_REPORT_READY`, `PAYMENT_RELEASED`, `PROOF_READY`, `MESSAGE_RECEIVED`.
- `models/models_extended.py` — Extended notification preferences (per-user, per-event toggle fields).
- `models/models_push.py` — FCM-ready push notification device registration.
- `services/` — `create_notification()`, `notify_report_ready()`, `notify_client_report_available()`, `notify_report_upcoming()`, `notify_log_submitted()`. All called from Celery tasks.
- `tasks.py` — Celery tasks for async email delivery.

---

### 5.8 `apps/search/` — Full-Text Search

**What it does:** Provides fast, Elasticsearch-backed full-text search across projects and freelancer profiles.

**Key Files:**
- `documents.py` — Two Elasticsearch DSL documents:
  - `ProjectDocument` — Indexes `Project` (title, description, budget, skills, client info) into the `projects` index.
  - `FreelancerDocument` — Indexes `FreelancerProfile` (bio, skills, hourly_rate, name, email) into the `freelancers` index.
- `signals.py` — Listens to `post_save` and `post_delete` on Project/FreelancerProfile to keep the Elasticsearch index in sync automatically.
- `selectors.py` — Query builders that use ES DSL for complex multi-field searches with filters.
- `services/` — Search history tracking, saved searches, autocomplete suggestions.

---

## 6. `core/` — Shared Infrastructure

The `core` app holds shared components used across all 8 domain apps. It enforces DRY and keeps cross-cutting concerns centralized.

| File | Purpose |
|---|---|
| `middleware.py` | 4 middleware classes: `RequestLoggingMiddleware` (logs every request with timing), `SecurityHeadersMiddleware` (XSS, content-type, referrer), `RateLimitMiddleware` (Redis-backed 100/hr anon, 1000/hr user), `CORSCustomMiddleware` (fine-grained CORS per origin) |
| `middleware_shutdown.py` | `GracefulShutdownMiddleware` — Sits first in the chain. Rejects new requests with 503 during graceful shutdown, letting in-flight requests complete. |
| `exceptions.py` | Custom `BusinessError`, `PermissionDeniedError`, `NotFoundError`, `ValidationError` hierarchy. `custom_exception_handler` for DRF normalizes all errors to `{"error": "...", "code": "...", "field": "..."}` format. |
| `cache.py` | Helper functions for Redis cache operations. |
| `decorators.py` | Reusable view/function decorators. |
| `pagination.py` | `StandardResultsPagination` — Enforces consistent pagination across all DRF viewsets. |
| `permissions.py` | Shared DRF `IsClient`, `IsFreelancer`, `IsOwner` permission classes. |
| `throttles.py` | Custom auth throttle (5/min) and OAuth throttle (10/min). |
| `sanitizers.py` | Input sanitization helpers against XSS and injection. |
| `health.py` | `/health/live/` and `/health/ready/` endpoints for Docker/load balancer health checks. |
| `utils.py` | General helpers, including `calculate_platform_cut()` used by payment tasks. |

---

## 7. `config/` — Project Configuration

| File | Purpose |
|---|---|
| `settings/base.py` | Core settings: 8 local apps, JWT (60min/7day, rotation, blacklist), Redis channels (1500 capacity, 24h group expiry), Celery 3-queue setup, Celery Beat schedule (3 periodic tasks), Razorpay keys, Azure Blob, Groq API, Elasticsearch DSL, SMTP email, Django Axes (5 failures, 5-min lockout), centralized rotating log file (10MB × 5 backups). |
| `settings/local.py` | SQLite fallback, DEBUG=True, relaxed CORS. |
| `settings/production.py` | HTTPS enforcement, HSTS, Sentry DSN wiring. |
| `settings/test.py` | In-memory DB, disabled migrations for speed. |
| `asgi.py` | Routes HTTP → Django WSGI app, `ws://` → `ChatConsumer` via `ProtocolTypeRouter`. Registers SIGTERM/SIGINT for graceful ASGI shutdown. |
| `celery.py` | Creates the Celery app. Defines 3 queues: `freelanceflow` (default), `freelanceflow_high_priority` (payment tasks), `freelanceflow_low_priority` (PDF, AI, report tasks). Routes specific tasks to appropriate queues. Registers graceful shutdown signal handlers. |
| `urls.py` | Root dispatcher: `/api/users/`, `/api/projects/`, `/api/bidding/`, `/api/bids/`, `/api/contracts/`, `/api/payments/`, `/api/worklogs/`, `/api/messaging/`, `/api/notifications/`, `/api/search/`. |
| `gunicorn_config.py` | Gunicorn worker count, timeout, logging config for production. |

---

## 8. Celery Task Architecture

```
Queue: freelanceflow_high_priority
  ├── process_razorpay_webhook_task    (payment webhook processing)
  ├── razorpay_transfer_to_freelancer_task  (payout via RazorpayX)
  └── process_razorpay_refund_task     (refund handling)

Queue: freelanceflow (default)
  ├── notify_freelancer_report_ready
  ├── notify_client_new_report
  ├── notify_client_log_submitted
  └── notify_freelancer_report_upcoming

Queue: freelanceflow_low_priority
  ├── generate_ai_report_task          (LangGraph → Groq → WeeklyReport)
  ├── generate_pdf_task                (WeasyPrint → Azure Blob)
  ├── generate_proof_pdf_task          (Delivery proof PDF)
  ├── trigger_scheduled_reports        (Beat: 00:05 daily)
  ├── check_upcoming_report_deadlines  (Beat: 09:00 daily)
  └── generate_weekly_reports_for_all_contracts  (Beat: Sunday 23:59)
```

**Task Reliability:** All payment tasks use `max_retries=3`. AI/PDF tasks use `max_retries=2-3` with exponential backoff. Workers use `task_acks_late=True` and `task_reject_on_worker_lost=True` to prevent task loss on crashes.

---

## 9. AI Pipeline Details

### Graph 1 — Interactive Chat Agent (Deliverable Creation)
- **Trigger:** `POST /api/worklogs/ai-chat/message/`
- **Service:** `groq_service.py` → `GroqChatService`
- **Model:** Groq Llama 3.3 70B Versatile
- **Graph:** `ChatAgentState` with conditional routing:
  - Node: `ask_follow_up` → continues conversation
  - Node: `generate_report` → produces structured JSON deliverable
- **Async:** View uses `sync_to_async` to keep ASGI non-blocking
- **Fallback:** Direct `groq.chat.completions.create()` → then static template

### Graph 2 — Automated Weekly Report Pipeline
- **Trigger:** Celery Beat daily or manual `POST /api/worklogs/report-schedule/{id}/generate-now/`
- **Service:** `ai_service.py`
- **Graph:** 3 sequential nodes:
  1. `gather_logs` — Fetches all WorkLogs for the period from DB
  2. `build_prompt` — Constructs structured prompt from logs
  3. `generate_report` — Calls Groq API → 3-section Markdown (SUMMARY / DETAILS / NEXT STEPS)
- **Result:** Saved to `WeeklyReport.ai_summary`, then PDF generated and uploaded to Azure Blob
- **Monitoring:** LangSmith `@traceable` on every graph entry point

---

## 10. Security Architecture

| Mechanism | Implementation |
|---|---|
| **Authentication** | JWT (SimpleJWT) — Bearer token in `Authorization` header |
| **WebSocket Auth** | JWT in `?token=` query param (validated per-connection) |
| **Token Rotation** | Refresh tokens rotated and blacklisted on every use |
| **Brute Force** | Django Axes — 5 failures → 5-minute lockout (DB handler) |
| **Rate Limiting** | DRF throttles (100/hr anon, 1000/hr user) + auth endpoints (5/min) |
| **Payment Security** | Razorpay HMAC-SHA256 signature verification on all webhooks |
| **Webhook Idempotency** | `PaymentEvent.event_id` unique constraint prevents double-processing |
| **RBAC** | `CLIENT` / `FREELANCER` role enforcement throughout all views |
| **CORS** | `django-cors-headers` + custom CORS middleware |
| **Security Headers** | X-Content-Type-Options, X-XSS-Protection, Referrer-Policy |
| **Input Sanitization** | `core/sanitizers.py` — XSS and injection protection |
| **CSRF** | Standard Django CSRF with custom cookie names (`ff_csrftoken`) |
| **Session** | DB-backed sessions, 7-day age, Lax SameSite |

---

## 11. Data Model Relationships

```
User (CLIENT or FREELANCER)
  ├── FreelancerProfile (1:1)
  └── ClientProfile (1:1)

Project (by CLIENT)
  ├── ProjectSkill (1:N)
  └── Bid (1:N by FREELANCER)
       └── Contract (1:1)
            ├── ReportSchedule (1:1)
            ├── WorkLog (1:N — daily logs)
            ├── WeeklyReport (1:N — AI reports)
            ├── Deliverable (1:N — formal submissions)
            ├── DeliveryProof (1:1 — final tamper-evident proof)
            ├── Conversation (1:1 → Message 1:N)
            └── Payment (1:1)
                 ├── PaymentEvent (1:N — idempotency log)
                 ├── PlatformEarning (1:1 — platform cut record)
                 └── PaymentMilestone (1:N)
```

---

## 12. API Endpoint Map

| Prefix | App | Key Endpoints |
|---|---|---|
| `/api/users/` | users | Register, Login, Refresh, Logout, Profile, Change Password, Reset Password, Google OAuth, Verify Email, Deactivate |
| `/api/projects/` | projects | CRUD Projects, Add/Remove Skills, Browse Open Projects |
| `/api/bidding/` | bidding | Submit Bid, Accept/Reject Bid, View Bids for Project |
| `/api/bids/` | bidding | Alias: freelancer's own bids |
| `/api/contracts/` | bidding | Alias: active contracts, contract detail, amendments, termination |
| `/api/payments/` | payments | Create Escrow, Release Payment, Refund, Webhook, Payment Status |
| `/api/worklogs/` | worklogs | Submit WorkLog, Approve/Reject Log, List Logs, AI Chat Message, View Reports, Report Schedule CRUD, Generate Now, Deliverable CRUD |
| `/api/messaging/` | messaging | List/Create Conversations, Message History |
| `/api/notifications/` | notifications | List Notifications, Mark Read, Preferences |
| `/api/search/` | search | Search Projects, Search Freelancers, Search History, Saved Searches, Autocomplete |
| `ws://host:8001/ws/chat/<contract_id>/` | messaging | Real-time contract chat |

---

## 13. Logging System

All logs go to a single rotating file: `logs/freelanceflow.log`

- **Format:** `[timestamp] LEVEL logger_name: message`
- **Rotation:** 10MB per file, 5 backup files kept
- **Per-app named loggers:** `apps.users`, `apps.projects`, `apps.bidding`, `apps.payments`, `apps.worklogs`, `apps.messaging`, `apps.notifications`, `apps.search`
- **Response time header:** Every HTTP response gets `X-Response-Time: Xms` injected by `RequestLoggingMiddleware`
- **Production:** JSON format handler (overrides plain-text)
- **Sentry:** All unhandled exceptions in production go to Sentry DSN

---

## 14. Docker Services

| Container | Port | Command |
|---|---|---|
| `redis` | 6379 | `redis-server --save 60 1 --maxmemory 256mb --maxmemory-policy allkeys-lru` |
| `elastic` | 9200 | Elasticsearch 8.14 (single node, security disabled for dev) |
| `web` | 8000 | `python manage.py runserver 0.0.0.0:8000` |
| `daphne` | 8001 | `daphne -b 0.0.0.0 -p 8001 config.asgi:application` |
| `celery` | — | Worker consuming all 3 queues, max 1000 tasks/child |
| `celery-beat` | — | `DatabaseScheduler` (schedules stored in DB) |
| `flower` | 5555 | Celery monitoring UI |

**Profile System:**
- `docker compose up -d` → **Infrastructure only** (Redis + Elasticsearch) — Use this for local dev where you run Django and Celery natively.
- `docker compose --profile app up --build -d` → **Full stack** — All 7 containers.

---

## 15. How to Run the Project

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for Redis + Elasticsearch)
- Node.js 18+ (for frontend)
- Valid credentials for: Groq API, Razorpay, Azure Blob Storage (or AWS S3), PostgreSQL (Supabase or local)

---

### Option A: Local Development (Recommended for Backend Work)

**Step 1 — Start Infrastructure (Redis + Elasticsearch)**
```bash
# In the project root
docker compose up -d
# Starts Redis on :6379 and Elasticsearch on :9200
```

**Step 2 — Python Environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements/base.txt
```

**Step 3 — Environment Variables**
```bash
cp .env.example .env
# Open .env and fill in:
# - SECRET_KEY (generate a strong one)
# - DATABASE_URL (Supabase PostgreSQL URL or leave as sqlite for dev)
# - REDIS_URL=redis://localhost:6379/0
# - CELERY_BROKER_URL=redis://localhost:6379/1
# - CELERY_RESULT_BACKEND=redis://localhost:6379/2
# - GROQ_API_KEY (from console.groq.com)
# - RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET / RAZORPAY_WEBHOOK_SECRET
# - AZURE_STORAGE_CONNECTION_STRING / AZURE_CONTAINER_NAME
# - EMAIL_HOST / EMAIL_PORT / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD
# - GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET (for OAuth)
# - ELASTICSEARCH_URL=http://localhost:9200
# - FRONTEND_URL=http://localhost:5173
```

**Step 4 — Database Migrations**
```bash
python manage.py migrate
python manage.py createsuperuser
```

**Step 5 — (Optional) Set Up Elasticsearch Indexes**
```bash
python manage.py search_index --rebuild
# OR run the setup script:
bash scripts/elasticsearch_setup.sh
```

**Step 6 — Run the Django Dev Server**
```bash
python manage.py runserver
# API available at: http://localhost:8000/api/
# Admin panel at:   http://localhost:8000/admin/
```

**Step 7 — Run Celery Worker (New Terminal)**
```bash
# Activate venv first
celery -A config worker -l info -Q freelanceflow,freelanceflow_high_priority,freelanceflow_low_priority
```

**Step 8 — Run Celery Beat (New Terminal)**
```bash
# Activate venv first
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Step 9 — Run Frontend (New Terminal)**
```bash
cd frontend/
npm install
npm run dev
# Frontend at: http://localhost:5173
```

---

### Option B: Full Docker Stack

```bash
# Build and start all 7 containers
docker compose --profile app up --build -d

# Check status
docker compose ps

# View logs
docker compose logs -f web
docker compose logs -f celery
```

**Service URLs:**
| Service | URL |
|---|---|
| Frontend (React) | http://localhost:5173 |
| REST API (Django) | http://localhost:8000/api/ |
| Admin Panel | http://localhost:8000/admin/ |
| WebSocket (Daphne) | ws://localhost:8001/ws/ |
| Celery Monitoring (Flower) | http://localhost:5555 |
| Elasticsearch | http://localhost:9200 |
| Redis | localhost:6379 |

---

### Option C: Makefile Shortcuts

```bash
make backend        # Starts Django REST API server
make frontend-dev   # Starts React Vite dev server
make worker         # Starts Celery worker
make test-auth      # Runs auth tests (--keepdb flag)
make help           # Shows all available commands
```

---

### Running Tests

```bash
# All tests
pytest

# Specific app tests
pytest apps/users/tests/
pytest apps/payments/tests/

# With verbose output
pytest -v --tb=short

# Keep test DB between runs (faster)
pytest --keepdb
```

---

## 16. Required Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Django secret key |
| `DEBUG` | ✅ | `True` for local, `False` for production |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `REDIS_URL` | ✅ | Redis URL for cache + channels |
| `CELERY_BROKER_URL` | ✅ | Redis URL for Celery broker |
| `CELERY_RESULT_BACKEND` | ✅ | Redis URL for Celery results |
| `GROQ_API_KEY` | ✅ | From [console.groq.com](https://console.groq.com) |
| `RAZORPAY_KEY_ID` | ✅ | Razorpay dashboard API key |
| `RAZORPAY_KEY_SECRET` | ✅ | Razorpay dashboard API secret |
| `RAZORPAY_WEBHOOK_SECRET` | ✅ | For HMAC-SHA256 webhook verification |
| `RAZORPAY_ACCOUNT_NUMBER` | ✅ | RazorpayX account for payouts |
| `AZURE_STORAGE_CONNECTION_STRING` | ✅ | Azure Blob Storage connection string |
| `AZURE_CONTAINER_NAME` | ❌ | Defaults to `media` |
| `EMAIL_HOST` | ✅ | SMTP host |
| `EMAIL_HOST_USER` | ✅ | SMTP user |
| `EMAIL_HOST_PASSWORD` | ✅ | SMTP password |
| `GOOGLE_CLIENT_ID` | ❌ | For Google OAuth (optional) |
| `GOOGLE_CLIENT_SECRET` | ❌ | For Google OAuth (optional) |
| `ELASTICSEARCH_URL` | ❌ | Defaults to `http://localhost:9200` |
| `FRONTEND_URL` | ❌ | Defaults to `http://localhost:3000` |
| `LANGSMITH_API_KEY` | ❌ | AI tracing (optional) |
| `SENTRY_DSN` | ❌ | Production error tracking |

---

## 17. Key Design Decisions

1. **Modular Monolith:** 8 distinct Django apps with isolated models, services, and serializers. Easy to extract to microservices if needed.
2. **Service Layer Pattern:** Views are thin; all business logic lives in `services/`. Serializers only validate and transform. Queries live in `selectors.py`.
3. **Three-Queue Celery:** Payment tasks (highest reliability needed) isolated from AI/PDF tasks (low priority, slow). Prevents payment processing from being starved by slow PDF rendering.
4. **Idempotent Webhooks:** `PaymentEvent.event_id` unique constraint ensures Razorpay webhook double-delivery never causes double payouts.
5. **Async ASGI WebSockets:** All ORM calls in WebSocket consumers are wrapped in `database_sync_to_async` — the event loop is never blocked.
6. **Graceful Shutdown:** Custom middleware + ASGI/Celery signal handlers ensure in-flight requests and tasks complete cleanly on deploy.
7. **Azure over S3 for PDFs:** AWS S3 is kept for legacy compatibility, but all new PDF uploads go through Azure Blob Storage with 7-day SAS URLs.
8. **AI Fallback Chain:** LangGraph → direct Groq API → static template. Never fails silently.
