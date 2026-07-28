# FreelanceFlow — High-Level Design

**Version:** 6.0.0  
**Last Updated:** June 11, 2026  
**Architecture:** Modular Monolith · Django 4.2 · PostgreSQL · Redis · Elasticsearch  
**Source of truth:** Derived from live backend code scan

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [System Overview](#2-system-overview)
3. [Architecture Decision — Modular Monolith](#3-architecture-decision--modular-monolith)
4. [System Architecture](#4-system-architecture)
5. [Component Breakdown](#5-component-breakdown)
6. [Data Model — Every Table in the Codebase](#6-data-model--every-table-in-the-codebase)
7. [API Surface](#7-api-surface)
8. [Core Data Flows](#8-core-data-flows)
9. [Authentication & Security](#9-authentication--security)
10. [Payment System Design](#10-payment-system-design)
11. [AI Integration Architecture](#11-ai-integration-architecture)
12. [Async Task System (Celery)](#12-async-task-system-celery)
13. [Real-Time Messaging (WebSocket)](#13-real-time-messaging-websocket)
14. [Search Architecture (Elasticsearch)](#14-search-architecture-elasticsearch)
15. [Cloud File Storage (Azure Blob Storage / S3)](#15-cloud-file-storage-azure-blob-storage--s3)
16. [Caching Strategy](#16-caching-strategy)
17. [Custom Middleware Stack](#17-custom-middleware-stack)
18. [Design Patterns](#18-design-patterns)
19. [Edge Cases & Concurrency](#19-edge-cases--concurrency)
20. [Deployment Architecture](#20-deployment-architecture)
21. [Observability & Monitoring](#21-observability--monitoring)
22. [Technology Stack](#22-technology-stack)
23. [Environment Variables Reference](#23-environment-variables-reference)
24. [Local Development Setup](#24-local-development-setup)
25. [Implemented vs Future Features](#25-implemented-vs-future-features)

---

## 1. Problem Statement

Traditional freelance platforms suffer from three core trust failures:

| Problem | Impact |
|---|---|
| **Upfront payment risk** | Clients pay before work — no delivery guarantee |
| **Non-payment risk** | Freelancers complete work but never get paid |
| **Work opacity** | No transparent audit trail of work performed |

**FreelanceFlow** solves all three:
- **Escrow-based payments** — Razorpay holds funds until client approves the deliverable
- **AI-powered documentation** — Groq Llama 3.3 70B converts natural conversations into structured, verifiable work reports
- **Formal delivery workflow** — Deliverables go through `DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED/REJECTED/REVISION_REQUESTED`

---

## 2. System Overview

Eight Django apps, each with strict domain boundaries:

| App | Domain |
|---|---|
| `apps.users` | Registration, JWT auth, Google OAuth2, profiles, activity log, online status |
| `apps.projects` | Project CRUD, categories, bookmarks, drafts, public share links |
| `apps.bidding` | Bid submission, contract creation, counter-offers, amendments |
| `apps.payments` | Escrow, release, refunds, disputes, milestones, invoices, multi-currency, tax docs |
| `apps.worklogs` | Daily logs (screenshot upload), AI chat, deliverables, weekly reports, delivery proof PDF, time-off |
| `apps.messaging` | Real-time WebSocket chat per contract |
| `apps.notifications` | In-app, email, push (FCM), notification preferences, digest emails, system announcements |
| `apps.search` | Elasticsearch-powered search, search history, saved searches, autocomplete suggestions |

Plus a `core` app with shared: `exceptions`, `pagination`, `middleware`, `utils`, `permissions`.

---

## 3. Architecture Decision — Modular Monolith

### Why Not Microservices?

| Factor | Monolith (current) | Microservices (future) |
|---|---|---|
| Team size | 1–10 devs ✅ | 50+ devs |
| Deployment | Single pipeline ✅ | Per-service CI/CD |
| Data consistency | ACID transactions ✅ | Eventual consistency |
| Network latency | In-process calls ✅ | HTTP/gRPC overhead |
| Debugging | Single log stream ✅ | Distributed tracing required |
| Infrastructure cost | 1 server ✅ | N services + service mesh |

**When to revisit:** Team > 50 devs, or specific module needs independent scaling (e.g., AI service CPU burst, payment SLA isolation).

### Module Communication Patterns

```python
# 1. Tight coupling (same transaction)
from apps.payments.services import create_escrow
payment = create_escrow(contract, client)

# 2. Loose coupling (Django Signals — cross-module side effects)
from django.db.models.signals import post_save
@receiver(post_save, sender=Contract)
def on_contract_created(sender, instance, created, **kwargs): ...

# 3. Async coupling (Celery — deferred I/O, never blocks the request)
transaction.on_commit(lambda:
    razorpay_transfer_to_freelancer_task.delay(payment.id, amount)
)
```

---

## 4. System Architecture

### Level 1 — System Context

```
┌──────────────────────────────────────────────────────────┐
│                       Internet Users                      │
│         ┌─────────────┐          ┌─────────────┐         │
│         │   Clients   │          │ Freelancers │         │
│         └──────┬──────┘          └──────┬──────┘         │
│                └──────────┬─────────────┘                 │
└───────────────────────────┼──────────────────────────────┘
                            │ HTTPS / WSS
                            ▼
               ┌───────────────────────┐
               │      FreelanceFlow    │
               │   (Marketplace API)   │
               └───────────┬───────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Razorpay   │  │   Groq AI    │  │   AWS S3     │
│  Payments +  │  │  LangChain   │  │  PDFs, logs, │
│  RazorpayX   │  │  LangGraph   │  │  screenshots │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Level 2 — Container Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                       FreelanceFlow System                     │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              React SPA (Frontend)                        │  │
│  │  Client Dashboard · Freelancer Dashboard · AI Chat UI   │  │
│  │  Razorpay Checkout · Real-time Chat · Project Search    │  │
│  └─────────────────────────┬───────────────────────────────┘  │
│                             │ HTTPS / WSS                      │
│  ┌──────────────────────────▼──────────────────────────────┐  │
│  │                    Nginx (Reverse Proxy)                  │  │
│  │  SSL · Rate Limiting · Static Files · WS Proxy           │  │
│  └──────┬──────────────────┬────────────────────────────────┘  │
│         │ HTTP             │ WS                                │
│  ┌──────▼──────┐   ┌───────▼──────┐   ┌──────────────────┐  │
│  │  Gunicorn   │   │   Daphne     │   │  Celery Workers  │  │
│  │  (WSGI)     │   │  (ASGI/WS)   │   │  + Celery Beat   │  │
│  │ Django REST │   │ Django Chan. │   │  Background jobs │  │
│  └──────┬──────┘   └───────┬──────┘   └────────┬─────────┘  │
│         └──────────────────┼────────────────────┘             │
│                             │                                  │
│  ┌──────────────────────────▼──────────────────────────────┐  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │  PostgreSQL  │  │    Redis     │  │Elasticsearch │  │  │
│  │  │  Primary DB  │  │ Cache/Broker │  │ projects +   │  │  │
│  │  │  ACID + ORM  │  │  Channels   │  │ freelancers  │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### Level 3 — Django Application Internals

**Consistent file structure across all 8 apps:**
```
apps/{app_name}/
├── models.py           ← Core domain schema
├── models_extended.py  ← Secondary models (activity logs, online status, bookmarks, disputes, etc.)
├── serializers.py      ← Input validation, response shaping
├── views.py            ← Thin HTTP controllers (delegate to services)
├── views_google_oauth.py ← Google OAuth2 init and callback handlers
├── services.py         ← Business logic, DB transactions, side effects
├── selectors.py        ← Optimised read queries (select_related/prefetch_related)
├── permissions.py      ← Object-level authorization
├── tasks.py            ← Celery background jobs
├── signals.py          ← Django signals (loose cross-module coupling)
├── logger.py           ← Per-app structured logger instance
└── urls.py             ← URL routing
```

---

## 5. Component Breakdown

### Backend Services

| Component | Key Responsibilities | Critical Implementation Details |
|---|---|---|
| **User Service** | Registration, JWT auth, profile CRUD, soft-delete (is_deactivated) | Email as USERNAME_FIELD. Roles: `CLIENT` / `FREELANCER`. `SubscriptionTier`: FREE / PRO. |
| **Google OAuth Service & Views** | Google OAuth2 initiation & callback JWT issuance | Exchange Google code for tokens, fetch profile, create/get User, issue SimpleJWT tokens & redirect to frontend. Throttled at 10 req/min. |

| **Activity Service** | Immutable audit log | `ActionType`: LOGIN, LOGOUT, PROJECT_CREATED, BID_PLACED, CONTRACT_SIGNED, PAYMENT_MADE, REVIEW_POSTED, PROFILE_UPDATED, PASSWORD_CHANGED |
| **Project Service** | CRUD, publish, cancel, draft saving, bookmarks, public share links | Status machine: DRAFT → OPEN → IN_PROGRESS → COMPLETED/CANCELLED. `ProjectShare` token for public links. |
| **Bidding Service** | Submit, accept, reject, withdraw bids, contract creation | `select_for_update()` on accept. All other PENDING bids bulk-rejected atomically. Cover letter minimum 50 chars. |
| **Payment Service** | Escrow, release, refunds, milestone release | Razorpay order created **outside** atomic block. `_get_razorpay_client()` is lazy-init. Decimal arithmetic throughout. |
| **Dispute Service** | `PaymentDispute` + `DisputeMessage` thread | Status: OPEN → UNDER_REVIEW → RESOLVED/CLOSED. Resolution: FAVOR_CLIENT, FAVOR_FREELANCER, SPLIT, REFUND. Evidence stored as JSONField URL list. |
| **Milestone Service** | Create, complete, approve, pay milestones | Total milestones validated ≤ contract amount. `percentage` auto-calculated. `get_milestone_progress()` returns aggregates. |
| **Invoice Service** | PDF invoice generation | WeasyPrint renders HTML template → PDF. Saves to `MEDIA_ROOT/invoices/`. Invoice number: `INV-{payment_id:06d}`. |
| **Tax Service** | `TaxDocument` generation (1099/W-9) | Total annual earnings aggregated from `Payment` model. PDF generation stubbed (URL stored). |
| **Multi-Currency Service** | `CurrencyExchangeRate`, `MultiCurrencyPayment` | `convert_currency()` reads rate from DB. Records original + converted amounts. |
| **Worklog Service** | Daily log CRUD, screenshot upload (ImageField → S3), approve/reject | `unique_together = ["contract", "date"]` — one log per contract per day. Validates 0.1–24 hours. |
| **Deliverable Service** | AI chat + submit + review cycle | Status: DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED / REJECTED / REVISION_REQUESTED. Stores full AI chat transcript as JSON. |
| **PDF Service** | Weekly report PDF + Delivery Proof PDF | WeasyPrint → in-memory bytes → S3 `put_object` → pre-signed URL (7-day expiry). Falls back to placeholder URL if S3 not configured. |
| **Time-Off Service** | Leave tracking | `LeaveType`: VACATION, SICK, PERSONAL, OTHER. Requires client approval. |
| **Messaging Service** | Per-contract chat | Daphne + Django Channels. Redis channel layer groups: `chat_{contract_id}`. |
| **Notification Service** | In-app, email, per-event preferences | `Notification.Type`: BID_SUBMITTED, BID_ACCEPTED, ESCROW_CREATED, LOG_SUBMITTED, REPORT_READY, PAYMENT_RELEASED, PROOF_READY, MESSAGE_RECEIVED |
| **Push Notification Service** | Browser push via FCM | `PushSubscription` stores browser subscription JSON. `NotificationPreference` per-event opt-in/out for email + push + in-app. |
| **Digest Service** | Scheduled digest emails | `DigestEmail` tracks sends. Frequency: DAILY/WEEKLY/MONTHLY. |
| **Announcement Service** | Platform-wide system announcements | `SystemAnnouncement` with target: all/freelancers/clients. Types: INFO, WARNING, MAINTENANCE, FEATURE. |
| **Search Service** | Full-text ES search + history + saved searches + autocomplete | `SearchHistory` + `SavedSearch` + `SearchSuggestion` (populated via popularity field). |
| **AI Service (Groq)** | Worklog generation via LangGraph | `groq_service.py` (20 KB) + `ai_service.py` (weekly reports). Groq Llama 3.3 70B. LangSmith tracing. Fallback to direct Groq API. |

### Infrastructure Components

| Component | Role |
|---|---|
| **PostgreSQL 15** | Primary ACID datastore, all domain data |
| **Redis 7** | Celery broker + result backend, Django Channels layer, session store, cache |
| **Elasticsearch 8** | Inverted index: `projects` index + `freelancers` index |
| **Celery + Beat** | Async background tasks + scheduled jobs |
| **Nginx** | SSL termination, static files, WS proxy (`proxy_pass ws://daphne:8001`) |
| **Gunicorn** | WSGI (REST API) |
| **Daphne** | ASGI (WebSocket) |
| **AWS S3** | Weekly report PDFs, delivery proof PDFs, worklog screenshots, invoice PDFs |
| **Razorpay** | Order creation, payment capture, HMAC webhook, RazorpayX payouts (IMPS mode) |
| **Groq API** | LLM inference (Llama 3.3 70B Versatile) |
| **LangSmith** | AI tracing, latency, token tracking |

---

## 6. Data Model — Every Table in the Codebase

### Entity Relationship Summary

```
User (1) ──── (1) FreelancerProfile      [freelancer_profiles]
User (1) ──── (1) ClientProfile          [client_profiles]
User (1) ──── (1) TwoFactorAuth          [two_factor_auth]
User (1) ──── (1) UserOnlineStatus       [user_online_status]
User (1) ──── (M) ActivityLog            [activity_logs]
User (1) ──── (M) Project                [as client]
User (1) ──── (M) Bid                    [as freelancer]
User (1) ──── (1) NotificationPreference [notification_preferences]
User (1) ──── (M) PushSubscription       [push_subscriptions]

Project (1) ── (M) Bid
Project (1) ── (M) ProjectSkill          [many-to-many via skill_name]
Project (1) ── (M) ProjectBookmark
Project (1) ── (1) ProjectShare          [share_token for public URL]
Project (1) ── (M) ProjectDraft          [draft saved separately]

Bid (1) ──── (1) Contract               [created on bid acceptance]

Contract (1) ── (1) Payment
Contract (1) ── (M) WorkLog
Contract (1) ── (M) Deliverable
Contract (1) ── (M) WeeklyReport
Contract (1) ── (1) DeliveryProof
Contract (1) ── (1) Conversation
Contract (1) ── (M) PaymentMilestone
Contract (1) ── (M) TimeOff

Payment (1) ── (1) Escrow
Payment (1) ── (M) PlatformEarning
Payment (1) ── (M) PaymentEvent          [webhook idempotency — unique razorpay_event_id]
Payment (1) ── (1) PaymentDispute
Payment (1) ── (1) MultiCurrencyPayment

PaymentDispute (1) ── (M) DisputeMessage

Conversation (1) ── (M) Message
```

### Complete Table Inventory

#### `apps.users`

| Table | Key Fields |
|---|---|
| `users` | email (unique), role (CLIENT/FREELANCER), is_active, is_deactivated, deactivated_at |
| `freelancer_profiles` | bio, skills (JSON list), hourly_rate, subscription_tier (FREE/PRO), total_earned, avatar, is_available, average_rating, total_reviews, razorpay_fund_account_id |
| `client_profiles` | company_name, total_spent, avatar, average_rating, total_reviews |
| `two_factor_auth` | is_enabled, secret_key (TOTP), backup_codes (JSON list of 10 hex codes) |
| `activity_logs` | action_type, description, ip_address, user_agent, metadata (JSON) |
| `user_online_status` | is_online, last_seen (auto_now) |

#### `apps.projects`

| Table | Key Fields |
|---|---|
| `projects` | title, description, budget, status (DRAFT/OPEN/IN_PROGRESS/COMPLETED/CANCELLED), deadline, client_id |
| `project_skills` | project_id, skill_name |
| `project_categories` | name, slug, description, icon, is_active |
| `project_bookmarks` | user_id, project_id, notes — unique_together |
| `project_drafts` | client_id, title, description, budget, deadline, skills (JSON), category_id |
| `project_shares` | project_id (OneToOne), share_token (unique 64-char), is_active, view_count, expires_at |

#### `apps.bidding`

| Table | Key Fields |
|---|---|
| `bids` | project_id, freelancer_id, amount, cover_letter, status (PENDING/ACCEPTED/REJECTED/WITHDRAWN) |
| `contracts` | bid_id (OneToOne), agreed_amount, start_date, end_date, is_active |
| `counter_offers` | bid_id, proposed_amount, message, status |
| `contract_amendments` | contract_id, amendment_type, description, status |

#### `apps.payments`

| Table | Key Fields |
|---|---|
| `payments` | contract_id (OneToOne), total_amount (Decimal), status (PENDING/ESCROWED/PAYOUT_PENDING/RELEASED/PAYOUT_FAILED/REFUNDED), razorpay_order_id, razorpay_payment_id, razorpay_payout_id, razorpay_refund_id, refund_amount, payout_error |
| `escrows` | payment_id (OneToOne), held_amount, refund_amount, released_at |
| `platform_earnings` | payment_id, cut_percentage, cut_amount |
| `payment_events` | payment_id, razorpay_event_id (unique), event_type — idempotency guard |
| `payment_disputes` | payment_id (OneToOne), disputer_id, reason, description, status (OPEN/UNDER_REVIEW/RESOLVED/CLOSED), resolution (FAVOR_CLIENT/FAVOR_FREELANCER/SPLIT/REFUND), resolution_notes, resolved_by, resolved_at, evidence_files (JSON list) |
| `dispute_messages` | dispute_id, sender_id, message, attachments (JSON) |
| `payment_milestones` | contract_id, title, description, amount, percentage, order, due_date, status (PENDING/IN_PROGRESS/SUBMITTED/APPROVED/PAID/REJECTED), razorpay_payment_id — unique_together (contract, order) |
| `tax_documents` | freelancer_id, document_type (1099/W9/OTHER), tax_year, total_earnings, document_url — unique_together (freelancer, tax_year, document_type) |
| `currency_exchange_rates` | from_currency, to_currency, rate (Decimal 6dp) — unique_together |
| `multi_currency_payments` | payment_id (OneToOne), original_currency, original_amount, converted_currency, converted_amount, exchange_rate, conversion_date |

#### `apps.worklogs`

| Table | Key Fields |
|---|---|
| `work_logs` | contract_id, freelancer_id, date, description, hours_worked (0.1–24), screenshot (ImageField), screenshot_url, reference_url, status (DRAFT/PENDING_APPROVAL/APPROVED/REJECTED), ai_generated_summary, client_notes, approved_at, approved_by — unique_together (contract, date) |
| `weekly_reports` | contract_id, week_start, week_end, ai_summary, pdf_url (S3), sent_to_client_at — unique_together (contract, week_start) |
| `deliverables` | contract_id, freelancer_id, title, description, ai_chat_transcript (JSON), ai_generated_report, attached_files (JSON), status (DRAFT/SUBMITTED/UNDER_REVIEW/APPROVED/REJECTED/REVISION_REQUESTED), submitted_at, reviewed_at, reviewed_by, client_feedback, revision_notes, hours_logged, payment_released |
| `delivery_proofs` | contract_id (OneToOne), pdf_url (S3), generated_at, total_hours, total_logs_count, total_deliverables, approved_deliverables, report_id (unique tamper-evident ID) |
| `time_offs` | freelancer_id, contract_id (optional), leave_type (VACATION/SICK/PERSONAL/OTHER), start_date, end_date, reason, status (PENDING/APPROVED/REJECTED), approved_by, approved_at |

#### `apps.messaging`

| Table | Key Fields |
|---|---|
| `messaging_conversation` | contract_id (OneToOne) |
| `messaging_message` | conversation_id, sender_id, content, attachments (JSON), is_read, created_at |

#### `apps.notifications`

| Table | Key Fields |
|---|---|
| `notifications` | recipient_id, title, body, type, is_read |
| `notification_preferences` | user_id (OneToOne), per-event toggles for email + push + in-app (21 boolean fields), weekly_digest |
| `push_subscriptions` | user_id, subscription_data (JSON), device_name, is_active |
| `digest_emails` | user_id, frequency (DAILY/WEEKLY/MONTHLY), content (JSON), sent_at |
| `system_announcements` | title, message, announcement_type (INFO/WARNING/MAINTENANCE/FEATURE), is_active, start_date, end_date, target_users (all/freelancers/clients), created_by |

#### `apps.search`

| Table | Key Fields |
|---|---|
| `search_history` | user_id, query, search_type (projects/freelancers/all), filters (JSON), results_count |
| `saved_searches` | user_id, name, query, search_type, filters (JSON), is_active |
| `search_suggestions` | term (unique), category (skill/project/location/other), popularity, is_active |

### Critical Database Indexes (Explicitly Defined in Code)

```python
# Composite indexes on high-traffic read paths
ActivityLog:       ["user", "-created_at"], ["action_type"]
PaymentMilestone:  ["contract", "status"], ["status"]
SearchHistory:     ["user", "-created_at"]
SearchSuggestion:  ["term"], ["-popularity"]
Notification:      ["recipient", "is_read"]
PaymentEvent:      ["razorpay_event_id"]  # unique — idempotency
```

### Payment Status State Machine

```
                    ┌──────────────────────────────────┐
                    │           PENDING                 │
                    │  (order created, not yet paid)    │
                    └──────────┬───────────────────────┘
                               │ signature verified
                               ▼
                    ┌──────────────────────────────────┐
                    │           ESCROWED               │
                    │  (funds held in Razorpay)        │
                    └──────────┬───────────────────────┘
                               │ client releases
                               ▼
                    ┌──────────────────────────────────┐
                    │        PAYOUT_PENDING            │
                    │  (RazorpayX payout queued)       │
                    └──────────┬──────────────┬────────┘
                    payout OK  │              │ payout fails
                               ▼              ▼
                    ┌────────────────┐  ┌──────────────────┐
                    │   RELEASED     │  │  PAYOUT_FAILED   │
                    └────────────────┘  └──────────────────┘

       ESCROWED ──[termination dispute]──► REFUNDED
```

### Deliverable Status State Machine

```
DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED
                                 → REJECTED
                                 → REVISION_REQUESTED → SUBMITTED (re-submit)
```

---

## 7. API Surface

### REST Endpoints

| Module | Base Path | Key Actions |
|---|---|---|
| **Auth** | `/api/users/` | `POST register/`, `POST login/`, `POST token/refresh/`, `POST logout/`, `GET me/`, `POST change-password/`, `POST verify-email/`, `POST password-reset/` |
| **Google OAuth** | `/api/users/` | `GET auth/google/`, `GET auth/google/callback/` |
| **Profiles** | `/api/users/` | `GET/PATCH freelancer-profile/`, `GET/PATCH client-profile/`, `GET online-status/` |
| **Projects** | `/api/projects/` | CRUD, `POST {id}/publish/`, `POST {id}/cancel/`, `GET {id}/bookmark/`, `GET share/{token}/` |
| **Project Drafts** | `/api/projects/` | `GET/POST/PATCH/DELETE drafts/` |
| **Bidding** | `/api/bidding/` | `POST bids/`, `POST bids/{id}/accept/`, `POST bids/{id}/reject/`, `DELETE bids/{id}/` (withdraw) |
| **Contracts** | `/api/bidding/` | `GET contracts/`, `GET contracts/{id}/`, `POST contracts/{id}/complete/`, `POST contracts/{id}/terminate/` |
| **Payments** | `/api/payments/` | `POST escrow/`, `POST verify/`, `POST release/`, `POST webhook/` |
| **Disputes** | `/api/payments/` | `GET disputes/`, `POST disputes/`, `POST disputes/{id}/resolve/` |
| **Milestones** | `/api/payments/` | `POST milestones/`, `POST milestones/{id}/complete/`, `POST milestones/{id}/release/` |
| **Invoices** | `/api/payments/` | `GET invoices/{payment_id}/`, `GET invoices/{payment_id}/pdf/` |
| **Worklogs** | `/api/worklogs/` | CRUD, `POST {id}/submit/`, `POST {id}/approve/`, `POST {id}/reject/` |
| **Deliverables** | `/api/worklogs/` | `POST deliverables/`, `POST deliverables/{id}/submit/`, `POST deliverables/{id}/approve/`, `POST deliverables/{id}/reject/`, `POST deliverables/{id}/request-revision/` |
| **AI Chat** | `/api/worklogs/` | `POST ai-chat/message/`, `POST ai-chat/generate-deliverable/` |
| **Weekly Reports** | `/api/worklogs/` | `GET weekly-reports/`, `GET weekly-reports/{id}/`, `GET weekly-reports/{id}/pdf/` |
| **Time-Off** | `/api/worklogs/` | `GET/POST time-off/`, `POST time-off/{id}/approve/` |
| **Messaging** | `/api/messaging/` | `GET conversations/`, `GET conversations/{id}/`, `POST messages/` |
| **Notifications** | `/api/notifications/` | `GET /`, `PATCH {id}/mark-read/`, `DELETE {id}/`, `GET preferences/`, `PATCH preferences/` |
| **Search** | `/api/search/` | `GET projects/`, `GET freelancers/`, `GET history/`, `GET saved/`, `GET suggestions/` |
| **Docs** | `/api/docs/` | Swagger UI — **local/dev only** (`DEBUG=True`). Never registered in production. |

### WebSocket

| Path | Purpose |
|---|---|
| `ws://host/ws/chat/{contract_id}/?token={jwt}` | Bidirectional real-time chat per contract. Auth via JWT query param. Redis channel group `chat_{contract_id}`. |

### API Configuration (from `base.py`)

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultsPagination",
    "DEFAULT_FILTER_BACKENDS": [DjangoFilterBackend, SearchFilter, OrderingFilter],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/hour", "user": "1000/hour"},
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}
```

---

## 8. Core Data Flows

### 8.1 Payment Escrow → Release Flow

```
[CLIENT]                              [SYSTEM]                       [FREELANCER]
   │                                     │                                │
   ├── POST /payments/escrow/ ───────────►│                                │
   │                                     │  [OUTSIDE atomic]              │
   │                                     │  razorpay.order.create()       │
   │                                     │  [INSIDE atomic]               │
   │                                     │  Payment.create(PENDING)       │
   │                                     │  Escrow.create(held_amount)    │
   │                                     │◄────────────────────────────── │
   │ Razorpay checkout modal             │                                │
   ├── [User pays via Razorpay] ─────────►│                                │
   ├── POST /payments/verify/ ───────────►│                                │
   │                                     │  HMAC-SHA256 verify            │
   │                                     │  Payment: PENDING → ESCROWED   │
   │                                     │                                │
   │                      [Work happens — logs, AI chat, deliverables]    │
   │                                     │                                │
   ├── POST /payments/release/ ──────────►│                                │
   │                                     │  [atomic] select_for_update()  │
   │                                     │  Assert status == ESCROWED     │
   │                                     │  Payment: ESCROWED → PAYOUT_PENDING │
   │                                     │  PlatformEarning.create(10%)   │
   │                                     │  on_commit: payout task queued │
   │                                     │                                │
   │                         [Celery] razorpay_transfer_to_freelancer_task│
   │                                     │  RazorpayX payout (IMPS mode)  │
   │                                     │  Payment → RELEASED            │
   │                                     │  Escrow.released_at = now()    │
   │                                     │  Contract.is_active = False    │
   │                                     │  Project → COMPLETED           │
   │                                     │  Milestones → PAID             │
   │                                     │  generate_delivery_proof()     │
   │                                     │  Notification to freelancer    │
   │                                     │────────────────────────────────►│
```

### 8.2 AI Worklog Flow

```
Freelancer: "I built JWT auth component today"
    │
    ▼
POST /api/worklogs/ai-chat/message/ {message, chat_history, contract_id}
    │
    ▼
groq_service.chat()
    ├── LangGraph StateGraph
    │       ├── process_message_node → Groq Llama 3.3 70B
    │       └── check_intent_node → route: continue | generate_report | end
    │
    ├── LangSmith traces each step
    └── Fallback: direct Groq API if LangGraph fails
    │
    ▼
Response: {message: "What libraries did you use?", report_ready: false}
    │
    ▼
[Multiple rounds until report ready]
    │
    ▼
Response: {report_ready: true, report_data: {
    "title": "JWT Auth Component",
    "description": "...",
    "hours_worked": 4.0,
    "tasks_completed": ["JWT integration", "Login form", "Axios"],
    "technologies_used": ["React", "JWT", "Axios"],
    "blockers": [],
    "next_steps": ["Add refresh token rotation"]
}}
    │
    ▼
POST /api/worklogs/deliverables/ {contract_id, report_data, chat_transcript}
    → Deliverable (DRAFT) created with full ai_chat_transcript JSON
    │
    ▼
POST /api/worklogs/deliverables/{id}/submit/
    → DRAFT → SUBMITTED
    → Client notified
    │
    ▼
POST /api/worklogs/deliverables/{id}/approve/  [client]
    → APPROVED
    → WorkLog created from report
```

### 8.3 Weekly Report + PDF to S3 Flow

```
Celery Beat: every Sunday 11:59 PM
    │
    ▼
generate_weekly_reports_for_all_contracts()
    │ for each active contract with logs last week:
    ▼
generate_ai_report_task.delay(contract_id, week_start)
    │
    ├── ai_service.generate_weekly_report(contract_id, week_start)
    │       → Groq AI summarises all WorkLogs for the week
    │       → WeeklyReport.create(ai_summary=...)
    │
    └── generate_pdf_task.delay(report.id, 'weekly_report')
            │
            ├── WeasyPrint renders worklogs/weekly_report.html → bytes
            ├── boto3.put_object(Bucket, Key="reports/{contract_id}/week_{date}.pdf")
            ├── generate_presigned_url(ExpiresIn=604800)  ← 7 days
            └── report.pdf_url = presigned_url; report.save()
```

### 8.4 Delivery Proof PDF to S3

```
After payout task completes:
    │
    └── generate_delivery_proof(contract.id)
            ├── Aggregate: total_hours, total_logs_count, deliverables stats
            ├── DeliveryProof.create(report_id=uuid4(), ...)
            ├── WeasyPrint renders worklogs/delivery_proof.html → bytes
            ├── boto3.put_object(Key="proofs/{contract_id}/delivery_proof.pdf")
            └── presigned URL stored in DeliveryProof.pdf_url
```

### 8.5 JWT Authentication Flow

```
LOGIN:
  POST /api/users/login/ {email, password}
  → Django Axes: 5 failures in window → 5-min lockout
  → Validate credentials
  → access token (60 min) + refresh token (7 days)
  → Return {access, refresh, user}

AUTHENTICATED REQUEST:
  Authorization: Bearer <access_token>
  → JWTAuthentication: HMAC verify + expiry + blacklist check
  → User attached to request.user

TOKEN REFRESH:
  POST /api/users/token/refresh/ {refresh}
  → ROTATE_REFRESH_TOKENS=True → new pair issued
  → BLACKLIST_AFTER_ROTATION=True → old refresh token blacklisted

LOGOUT:
  POST /api/users/logout/ {refresh}
  → refresh token added to JWT blacklist table
```

---

## 9. Authentication & Security

### JWT Configuration (from `base.py`)

| Setting | Value |
|---|---|
| `ACCESS_TOKEN_LIFETIME` | 60 minutes |
| `REFRESH_TOKEN_LIFETIME` | 7 days |
| `ROTATE_REFRESH_TOKENS` | True |
| `BLACKLIST_AFTER_ROTATION` | True |
| `UPDATE_LAST_LOGIN` | True |
| `AUTH_HEADER_TYPES` | `("Bearer",)` |

### Security Middleware Stack (in order)

```python
GracefulShutdownMiddleware    # Must be first — catches SIGTERM
SecurityMiddleware            # Django built-in
CorsMiddleware                # django-cors-headers
RequestLoggingMiddleware      # core — structured request log
SecurityHeadersMiddleware     # core — HSTS, X-Frame-Options, CSP
CacheControlMiddleware        # core — sets no-cache on API responses
SessionMiddleware
CommonMiddleware
CsrfViewMiddleware
AuthenticationMiddleware
AxesMiddleware                # brute force — 5 attempts → lockout
MessageMiddleware
XFrameOptionsMiddleware
CORSCustomMiddleware          # core — additional CORS handling
```

### Object-Level Permissions (defined in each app's `permissions.py`)

```python
IsProjectOwner          # Only project.client can modify
IsContractParticipant   # Only client or freelancer on that contract
IsContractClient        # Approve deliverables, release payment
IsContractFreelancer    # Submit deliverables, create worklogs
IsWorkLogFreelancer     # Edit/delete own worklogs only
IsPaymentClient         # Trigger escrow release
IsPaymentParticipant    # View payment details
```

### Payment Security

```python
# HMAC-SHA256 webhook verification
razorpay_client.utility.verify_webhook_signature(
    raw_body_bytes, X_Razorpay_Signature_header, WEBHOOK_SECRET
)
# Invalid sig → HTTP 200 (prevents Razorpay retry flood, logs the event)
# Missing event_id → HTTP 400 (tells Razorpay to retry)

# Idempotency guard
if PaymentEvent.objects.filter(razorpay_event_id=event_id).exists():
    return  # already processed, skip

# Lazy Razorpay client (prevents startup crash when creds absent)
def _get_razorpay_client():
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Decimal arithmetic — no floats for money
refund_amount = (total * Decimal(str(pct)) / 100).quantize(
    Decimal('0.01'), rounding=ROUND_HALF_UP
)
```

---

## 10. Payment System Design

### Key Design Decisions

**1. Razorpay order created OUTSIDE `transaction.atomic()`**

If the DB write fails, we retry without creating a duplicate Razorpay order. If inside the transaction, a rollback wouldn't undo the Razorpay order.

**2. Payout triggered via `on_commit`**

```python
transaction.on_commit(lambda:
    razorpay_transfer_to_freelancer_task.delay(payment.id, amount)
)
```
Task only fires after DB transaction commits — prevents queuing a payout for a payment that never saved.

**3. Payout mode: IMPS via RazorpayX**

```python
payout_payload = {
    'account_number': RAZORPAY_ACCOUNT_NUMBER,
    'amount': int(Decimal(str(amount)) * 100),  # paise
    'currency': 'INR',
    'mode': 'IMPS',
    'purpose': 'payout',
    'fund_account_id': freelancer.freelancer_profile.razorpay_fund_account_id,
    'queue_if_low_balance': True,
    'reference_id': f'payment_{payment.id}',
}
```

**4. Platform cut recorded atomically with payout confirmation**

```python
PlatformEarning.objects.get_or_create(
    payment=payment,
    defaults={
        "cut_percentage": PLATFORM_CUT_PERCENTAGE,  # 10
        "cut_amount": total * Decimal('0.10'),
    },
)
```

**5. Multi-currency: model exists, `convert_currency()` reads from `CurrencyExchangeRate` DB table**

Rates are manually seeded — no live exchange rate API connected yet (see §25).

---

## 11. AI Integration Architecture

### Stack

| Layer | Technology |
|---|---|
| LLM | Groq API — Llama 3.3 70B Versatile |
| Orchestration | LangChain + LangGraph (`groq_service.py` — 20 KB) |
| Weekly reports | `ai_service.py` (separate, simpler pipeline) |
| Monitoring | LangSmith (traces every graph execution) |
| PDF export | WeasyPrint → bytes → S3 |

### LangGraph State Machine

```python
workflow = StateGraph(ChatAgentState)
workflow.add_node("process_message", process_message_node)  # Groq call
workflow.add_node("check_intent", check_intent_node)         # route decision
workflow.set_entry_point("process_message")
workflow.add_edge("process_message", "check_intent")
workflow.add_conditional_edges(
    "check_intent",
    lambda state: state["next_action"],
    {
        "continue":        END,   # AI asks clarifying question
        "generate_report": END,   # AI outputs structured JSON report
        "end":             END,   # Conversation done
    }
)
graph = workflow.compile()
```

**Fallback:** `groq_service.py` catches `LangGraphError` and falls back to a direct `groq.chat.completions.create()` call.

---

## 12. Async Task System (Celery)

### Architecture

```
Django Service Layer
    │
    ├── task.delay(args)         ──────────────────►  Redis Broker
    │                                                       │
    └── transaction.on_commit()                             ▼
         → task.delay()          ←────────  Celery Worker Pool
                                                            │
                                                    Execute + persist
                                                    result → Redis
```

### Task Inventory

| Task | File | Trigger | Retry |
|---|---|---|---|
| `razorpay_transfer_to_freelancer_task` | `payments/tasks.py` | Payment release (`on_commit`) | `bind=True, max_retries=3` |
| `process_razorpay_refund_task` | `payments/tasks.py` | Dispute termination | `bind=True, max_retries=3` |
| `process_razorpay_webhook_task` | `payments/tasks.py` | Webhook POST | None — idempotency-gated |
| `generate_ai_report_task` | `worklogs/tasks.py` | Celery Beat (Sunday 11:59 PM) | None |
| `generate_pdf_task` | `worklogs/tasks.py` | After AI report | None |
| `generate_proof_pdf_task` | `worklogs/tasks.py` | After payout released | None |
| `notify_freelancer_report_ready` | `worklogs/tasks.py` | After weekly report | None |
| `notify_client_log_submitted` | `worklogs/tasks.py` | On log submit | None |
| `generate_weekly_reports_for_all_contracts` | `worklogs/tasks.py` | Beat (Sunday 11:59 PM) | None |

### Celery Configuration (from `base.py`)

```python
CELERY_TASK_DEFAULT_QUEUE = "freelanceflow"
CELERY_TASK_ACKS_LATE = True             # Re-queue if worker dies mid-task
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1    # Fair scheduling
CELERY_TASK_TIME_LIMIT = 30 * 60        # 30-min hard kill
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60   # 25-min graceful stop
```

---

## 13. Real-Time Messaging (WebSocket)

### Architecture

```
Browser
  │ WSS
  ▼
Nginx → proxy_pass ws://daphne:8001
  │
  ▼
Daphne (ASGI)
  │
  ▼
Django Channels ChatConsumer
  │
  ├── connect():    JWT auth via query param, join Redis group "chat_{contract_id}"
  ├── receive():    save Message to PostgreSQL, broadcast to Redis group
  └── disconnect(): leave group
  │
  ▼
Redis Channel Layer → broadcast to all connected clients in group
```

---

## 14. Search Architecture (Elasticsearch)

### Indexes (defined in `apps/search/documents.py`)

**`projects` index:**
```python
class ProjectDocument(Document):
    client_name = TextField(attr="client.get_full_name")  # denormalized
    client_email = KeywordField(attr="client.email")
    skills = KeywordField(multi=True)
    status = KeywordField()
    # + id, title, description, budget, deadline, created_at, updated_at
    class Index:
        name = "projects"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}
```

**`freelancers` index:**
```python
class FreelancerDocument(Document):
    email = KeywordField(attr="user.email")
    full_name = TextField(attr="user.get_full_name")
    skills = KeywordField(multi=True)
    # + id, bio, hourly_rate, subscription_tier, total_earned, created_at
    class Index:
        name = "freelancers"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}
```

### Sync Strategy

- **Production:** `ELASTICSEARCH_DSL_AUTOSYNC=True` — saves trigger automatic re-index via `BaseSignalProcessor`
- **Local dev:** `ELASTICSEARCH_DSL_AUTOSYNC=False` — no ES instance required. Manual rebuild: `python manage.py search_index --rebuild`

---

## 15. Cloud File Storage (Azure Blob Storage / S3)

> 💡 **Production Infrastructure Note:** Future production deployment uses **Azure Blob Storage** for media, screenshots, and PDF storage (via `django-storages[azure]` or Azure SDK) hosted on an **Azure Virtual Machine (VM)**. S3 interfaces act as legacy/local compatibility wrappers.

### Objects Stored in Cloud Storage

| Object Type | Key / Blob Pattern | Access |
|---|---|---|
| Weekly report PDFs | `reports/{contract_id}/week_{week_start}.pdf` | Shared Access Signature (SAS) / Pre-signed URL |
| Delivery proof PDFs | `proofs/{contract_id}/delivery_proof.pdf` | SAS / Pre-signed URL (7-day expiry) |
| Worklog screenshots | `worklogs/screenshots/{YYYY}/{MM}/{DD}/{filename}` | Via Django `ImageField` / Azure Blob Storage |
| Invoice PDFs | `MEDIA_ROOT/invoices/invoice_{payment_id}_{date}.pdf` | Served via media URL / Azure Blob |
| Tax documents | Stored URL in `TaxDocument.document_url` | Manual / external |

### Upload Flow (PDF Service)

```python
def upload_to_cloud_storage(pdf_bytes: bytes, file_key: str) -> str:
    # Production Target: Azure Blob Storage (or S3 fallback)
    if not settings.AZURE_STORAGE_CONNECTION_STRING and not settings.AWS_ACCESS_KEY_ID:
        return f"https://placeholder-storage-url/{file_key}"  # local dev fallback

    # Uploads to Azure Blob Container / S3 Bucket and returns secure SAS/Pre-signed URL
    ...
```


---

## 16. Caching Strategy

| Cache Target | Backend | TTL | Invalidation |
|---|---|---|---|
| User profiles | Redis | 5 min | On profile update |
| Project details | Redis | 5 min | On project save |
| JWT blacklist | Redis (via simplejwt) | 7 days | Automatic (token TTL) |
| Session store | PostgreSQL | 7 days | On logout |
| Static files | Nginx | 1 year | Cache-busting filenames |

**Configuration:** `CACHES["default"]` points to Redis. `IGNORE_EXCEPTIONS=True` — cache failures are logged but never crash requests.

---

## 17. Custom Middleware Stack

Custom middleware in `core/`:

| Middleware | Purpose |
|---|---|
| `GracefulShutdownMiddleware` | Catches `SIGTERM`, drains in-flight requests before exit. Must be first in stack. |
| `RequestLoggingMiddleware` | Logs every request: method, path, status, duration, user_id. |
| `SecurityHeadersMiddleware` | Adds HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy. |
| `CacheControlMiddleware` | Sets `Cache-Control: no-store` on all API responses (prevents browser caching of JWT-protected data). |
| `CORSCustomMiddleware` | Supplements `corsheaders` with additional fine-grained origin handling. |

---

## 18. Design Patterns

### Service Layer (primary pattern)

Views are thin HTTP coordinators only. All business logic lives in `services.py`.

```python
# views.py — HTTP concern only
class ProjectCreateView(APIView):
    def post(self, request):
        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = create_project(client=request.user, **serializer.validated_data)
        return Response(ProjectSerializer(project).data, status=201)

# services.py — transaction + side effects + logging
def create_project(client, **data) -> Project:
    with transaction.atomic():
        project = Project.objects.create(client=client, **data)
        index_project_in_elasticsearch(project)
    logger.info("Project created: id=%s client_id=%s", project.id, client.id)
    return project
```

### Selector Pattern (read/write separation)

```python
# selectors.py
def get_project_with_bids(project_id: int) -> Project:
    return (
        Project.objects
        .select_related('client', 'category')
        .prefetch_related('skills', 'bids__freelancer__freelancer_profile')
        .get(id=project_id)
    )
```

### Lazy Factory (Razorpay client)

```python
def _get_razorpay_client():
    """Only instantiated at call time — never at module load."""
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
```

### Optimistic Locking via `select_for_update`

```python
with transaction.atomic():
    bid = Bid.objects.select_for_update().get(id=bid_id)
    if bid.status != 'PENDING':
        raise ValidationError("Bid already processed")
    bid.status = 'ACCEPTED'
    bid.save()
    Bid.objects.filter(project=bid.project, status='PENDING').update(status='REJECTED')
```

### Django Signals (loose coupling)

```python
# bidding/signals.py
@receiver(post_save, sender=Contract)
def on_contract_created(sender, instance, created, **kwargs):
    if created:
        create_notification(recipient=instance.bid.freelancer, ...)
```

### `on_commit` for Celery (prevent phantom tasks)

```python
transaction.on_commit(lambda:
    razorpay_transfer_to_freelancer_task.delay(payment.id, amount)
)
```

---

## 19. Edge Cases & Concurrency

| Scenario | Problem | Implementation |
|---|---|---|
| **Double bid accept** | Two clients hit accept simultaneously | `select_for_update()` + status assert inside `transaction.atomic()` |
| **Duplicate webhook** | Razorpay delivers same event twice | `PaymentEvent` unique on `razorpay_event_id` — skip if exists |
| **Razorpay order + DB fail** | Order created, DB write rolls back | Order created OUTSIDE atomic — safe to retry without duplicate order |
| **Phantom Celery task** | Payout queued before DB commit | `on_commit` — task only enqueued after successful commit |
| **Payout fails** | RazorpayX API error | `Payment → PAYOUT_FAILED`, `payout_error` field stores message. `max_retries=3`. |
| **Worker dies mid-payout** | Task half-executed | `ACKS_LATE=True` + `REJECT_ON_WORKER_LOST=True` → task re-queued |
| **S3 not configured** | PDF upload fails locally | `upload_to_s3()` returns placeholder URL if `AWS_ACCESS_KEY_ID` is empty |
| **ES not running (local dev)** | App crashes on model save | `AUTOSYNC=False` + `BaseSignalProcessor` — no ES calls in dev |
| **LangGraph unavailable** | AI chat fails | `groq_service` catches error → falls back to direct Groq API call |
| **AnonymousUser in schema introspection** | drf-spectacular crashes on `request.user.role` | `if getattr(self, "swagger_fake_view", False): return Model.objects.none()` in every `get_queryset` |
| **One log per day per contract** | Duplicate worklogs | `unique_together = ["contract", "date"]` at DB level |

---

## 20. Deployment Architecture

### Production Stack (AWS EC2)

```
Route 53 (DNS)
    │
    ▼
```
                                      Internet Traffic (Clients / Freelancers)
                                                         │
                                               ┌─────────▼─────────┐
                                               │   Cloudflare CDN  │
                                               └─────────┬─────────┘
                                                         │
                                               ┌─────────▼─────────┐
                                               │   Azure Load      │
                                               │   Balancer        │
                                               └─────────┬─────────┘
                                                         │
                                       ┌─────────────────┴─────────────────┐
                                       ▼                                   ▼
                       Azure Virtual Machine (VM 1)       Azure Virtual Machine (VM 2)
                         Linux / Nginx Reverse Proxy        Linux / Nginx Reverse Proxy
                         Gunicorn (WSGI / REST API)         Gunicorn (WSGI / REST API)
                         Daphne (ASGI / WebSockets)         Daphne (ASGI / WebSockets)
                         Celery Worker + Beat               Celery Worker
                                       │                                   │
                    ┌──────────────────┼───────────────────────────────────┤
                    ▼                  ▼                                   ▼
             PostgreSQL           Redis                               Elasticsearch
             (Supabase)       (Local / Upstash)                       (Search Node)
                    │
                    ▼
          Azure Blob Storage
            ├── freelanceflow-static-prod
            ├── freelanceflow-media-prod (Screenshots, Invoice PDFs)
            └── freelanceflow-reports-prod (Delivery Proofs, Weekly Reports)
```

### Settings Environment Matrix

| Setting | `local.py` | `production.py` |
|---|---|---|
| `DEBUG` | `True` | `False` |
| `drf_spectacular` | ✅ in `INSTALLED_APPS` | ❌ never loaded |
| Swagger UI | ✅ `/api/docs/` registered | ❌ URL block never runs |
| `DEFAULT_SCHEMA_CLASS` | ✅ `AutoSchema` | ❌ not set |
| Email backend | `console` | SMTP (AWS SES) |
| `ELASTICSEARCH_DSL_AUTOSYNC` | `False` | `True` |
| `SESSION_COOKIE_SECURE` | `False` | `True` |
| `SECURE_SSL_REDIRECT` | `False` | `True` |

### Quick Deploy (Render)

```bash
Build:  pip install -r requirements/production.txt
Start:  gunicorn config.wsgi:application
Env:    DJANGO_SETTINGS_MODULE=config.settings.production
```

---

## 21. Observability & Monitoring

### Implemented

| Tool | Coverage |
|---|---|
| **Structured logging** | Every service function logs at `INFO`/`ERROR` with `payment_id`, `contract_id`, `user_id` context. Per-app loggers: `apps.payments`, `apps.bidding`, `apps.worklogs`, etc. |
| **LangSmith** | Every Groq graph execution traced: latency, token usage, node path |
| **Sentry** | `SENTRY_DSN` configured in `production.py` — real-time exception alerts |
| **Celery task logging** | `logger.info` at task start + completion. `logger.error` + `exc_info=True` on failures. |
| **Nginx access logs** | Request rate, status codes, latency |

### Health Check

```
GET /health/
{
  "status": "healthy",
  "timestamp": "2026-06-11T11:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "elasticsearch": "healthy"
  }
}
```

### Planned (not yet implemented)

- Prometheus metrics endpoint → Grafana dashboards
- Loki log aggregation
- AlertManager → Slack/PagerDuty
- API response time p95/p99 tracking

---

## 22. Technology Stack

### Backend

| Technology | Version | Why |
|---|---|---|
| **Django** | 4.2 LTS | Batteries-included, mature ORM, security hardened |
| **Django REST Framework** | 3.x | Serializers, viewsets, throttling, pagination |
| **PostgreSQL** | 15 | ACID, JSONB, row-level locking |
| **Redis** | 7 | Unified: Celery broker + Channels layer + cache + sessions |
| **Celery** | 5.x | Background tasks, retry logic, Beat scheduler |
| **django-celery-beat** | — | Persistent periodic task schedule in DB |
| **Django Channels** | 4.x | WebSocket, ASGI |
| **Elasticsearch** | 8.x | Full-text search, BM25 scoring, keyword filters |
| **django-elasticsearch-dsl** | — | Model → ES document sync |
| **Razorpay** | — | Escrow orders, HMAC webhooks, RazorpayX payouts (IMPS) |
| **Groq API** | — | Llama 3.3 70B Versatile — fastest LLM inference |
| **LangChain + LangGraph** | — | Stateful multi-turn AI conversation |
| **LangSmith** | — | AI observability |
| **WeasyPrint** | — | HTML → PDF for weekly reports, delivery proofs, invoices |
| **Google OAuth2** | — | Single sign-on authentication flow & JWT token issuance |
| **drf-spectacular** | 0.29 | OpenAPI 3.1 — dev only, zero prod footprint |
| **django-axes** | — | Brute force protection |
| **django-environ** | — | 12-factor env config |
| **django-filter** | — | Query param filtering on list endpoints |
| **django-extensions** | — | Dev management commands |
| **boto3** | — | S3 uploads, pre-signed URLs |

### Frontend

| Technology | Why |
|---|---|
| **React 18** | Component model, Concurrent Mode |
| **Vite** | Sub-second HMR |
| **Tailwind CSS** | Utility-first design system |
| **Axios** | JWT interceptor, refresh logic |
| **React Router v6** | Nested + protected routes |

---

## 23. Environment Variables Reference

```bash
# Django
SECRET_KEY=
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=api.freelanceflow.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/freelanceflow

# Redis
REDIS_URL=redis://host:6379/0
CELERY_BROKER_URL=redis://host:6379/0
CELERY_RESULT_BACKEND=redis://host:6379/0

# Razorpay
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
RAZORPAY_ACCOUNT_NUMBER=          # RazorpayX payout source account

# AWS S3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=ap-south-1
AWS_CLOUDFRONT_DOMAIN=

# AI
GROQ_API_KEY=
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=freelanceflow
LANGSMITH_TRACING=True

# Elasticsearch
ELASTICSEARCH_URL=http://es:9200

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@freelanceflow.com

# App
FRONTEND_URL=https://freelanceflow.vercel.app
CORS_ALLOWED_ORIGINS=https://freelanceflow.vercel.app
PLATFORM_CUT_PERCENTAGE=10

# Monitoring
SENTRY_DSN=
```

---

## 24. Local Development Setup

```bash
# 1. Clone + virtual environment
python -m venv venv
venv\Scripts\activate             # Windows
source venv/bin/activate          # macOS/Linux

# 2. Install
pip install -r requirements/local.txt

# 3. Environment
cp .env.example .env
# Fill: DATABASE_URL, REDIS_URL, GROQ_API_KEY, RAZORPAY_*

# 4. Database + superuser
python manage.py migrate
python manage.py createsuperuser

# 5. Run
python manage.py runserver        # API:      http://localhost:8000
                                  # Swagger:  http://localhost:8000/api/docs/
                                  # Admin:    http://localhost:8000/admin/

# 6. Optional: Celery
celery -A config worker -l info
celery -A config beat -l info
celery -A config flower           # http://localhost:5555

# 7. Optional: Elasticsearch
# python manage.py search_index --rebuild
```

### Docker (Full Stack)

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Services:
# API:           http://localhost:8000
# Swagger UI:    http://localhost:8000/api/docs/
# Frontend:      http://localhost:3000
# PostgreSQL:    localhost:5432
# Redis:         localhost:6379
# Elasticsearch: localhost:9200
# Flower:        http://localhost:5555
```

---

## 25. Implemented vs Future Features

### ✅ Fully Implemented (confirmed by code scan)

**Core Platform**
- Email-based registration + JWT auth (access 60 min / refresh 7 days, rotation, blacklist)
- Role-based access: CLIENT / FREELANCER
- Google OAuth2 Single Sign-On flow (`/api/users/auth/google/` & `/api/users/auth/google/callback/`)
- Account soft-delete (`is_deactivated` flag)
- Subscription tier field: FREE / PRO (model exists — no billing logic yet)
- Immutable activity log (10 action types)
- User online status (DB-backed, updated via WebSocket)
- Project CRUD + publish/cancel lifecycle
- Project categories, bookmarks, drafts, public share links with view counter
- Bid submission (min 50-char cover letter, amount ≤ budget validation)
- Bid accept (atomic: `select_for_update`, bulk-reject other bids, auto-contract)
- Counter-offers, contract amendments (model + service level)
- Escrow payment via Razorpay (order outside atomic, local record inside atomic)
- Payment signature verification (HMAC-SHA256)
- Webhook processing with idempotency (`PaymentEvent` unique constraint)
- Automated payout via RazorpayX (IMPS, `queue_if_low_balance=True`)
- Payout failure handling (`PAYOUT_FAILED` status, error text stored)
- Platform earnings recording (configurable %, default 10%)
- Payment dispute model + thread (`DisputeMessage`)
- Milestone-based payments (create, complete, approve, release, progress tracking)
- Invoice PDF generation (WeasyPrint, `INV-{id:06d}` numbering)
- Multi-currency model (`CurrencyExchangeRate` + `MultiCurrencyPayment`)
- Tax document model (1099/W-9 per year per freelancer)
- Daily worklog with screenshot upload (`ImageField` to S3), hours 0.1–24, 1 per contract per day
- AI-powered deliverable creation (Groq Llama 3.3 70B via LangGraph)
- Deliverable 6-status lifecycle including `REVISION_REQUESTED`
- Weekly AI report generation (Celery Beat, Sunday 11:59 PM)
- Weekly report + delivery proof PDF → S3 (pre-signed 7-day URL)
- Freelancer time-off tracking (4 leave types, client approval)
- Real-time WebSocket chat (Daphne + Channels, Redis group per contract)
- In-app notifications (8 event types)
- Per-user notification preferences (email + push + in-app toggles per event type)
- Browser push notification subscriptions (FCM-ready model)
- Digest emails (DAILY/WEEKLY/MONTHLY model)
- System announcements (role-targeted: all/freelancers/clients)
- Elasticsearch full-text search: projects + freelancers indexes
- Search history, saved searches, autocomplete suggestions
- Custom middleware: graceful shutdown, request logging, security headers, cache-control
- OpenAPI 3.1 Swagger UI (dev-only — zero prod footprint)
- Structured per-app logging throughout services and tasks
- Sentry error tracking (production)
- LangSmith AI tracing

### 🚧 Models Exist — Service/API Incomplete

| Feature | What Exists | What's Missing |
|---|---|---|
| **Subscription / PRO tier** | `SubscriptionTier` field on `FreelancerProfile` (FREE/PRO) | No billing logic, no Stripe/Razorpay subscription integration |
| **Tax document PDF** | `TaxDocument` model, `generate_tax_document()` service | PDF generation is stubbed (`# generate_pdf(tax_doc)` is commented out) |
| **Multi-currency live rates** | `CurrencyExchangeRate` table, `convert_currency()` | No exchange rate API — rates must be manually seeded in DB |
| **Review/rating system** | `average_rating`, `total_reviews` fields on both profiles | No `Review` model, no API to submit reviews |
| **Push notifications** | `PushSubscription` model, `services_push.py` | FCM integration requires `VAPID_PUBLIC_KEY` env var — not wired in settings |
| **Admin dashboard** | Standard Django Admin | Not customized beyond basic registrations |

### ❌ Not Started — Future Roadmap

| Feature | Notes |
|---|---|
| **Mobile apps** | iOS / Android — React Native planned |
| **Video calls** | WebRTC integration |
| **Automated dispute resolution** | AI mediation agent |
| **Prometheus + Grafana** | Metrics collection + dashboards |
| **Loki log aggregation** | Centralized log shipping |
| **Advanced analytics** | Business metrics dashboard |
| **Automated skill verification** | Portfolio badges, credential checks |
| **AI project matching** | Automatic freelancer-project suggestions |
| **Referral program** | Credit-based referrals |
| **Multi-language** | i18n — `USE_I18N=True` is set but no translations |
| **Blockchain delivery proof** | Immutable on-chain record |
| **GitHub / Figma integrations** | OAuth-based tool connections |
| **S3 microservice** | Dedicated media service with independent scaling, CDN warming, virus scanning |

---

*Document Status: ✅ Single Source of Truth — derived from live code scan June 11, 2026*  
*Supersedes all previous HLD versions (v1–v5)*
