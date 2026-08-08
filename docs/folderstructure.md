# FreelanceFlow - Complete Folder & File Structure Guide

> A beginner-friendly, file-by-file explanation of the entire FreelanceFlow project.
> FreelanceFlow is a freelancing platform where clients post projects and freelancers bid on them.
> It has real-time chat, escrow payments (Razorpay), AI-powered work summaries, and more.

---

## Table of Contents

1. [Root Directory](#root-directory)
2. [config/ — Django Configuration](#config)
3. [core/ — Shared Utilities](#core)
4. [apps/ — Django Applications](#apps)
   - [apps/users/](#appsusers)
   - [apps/projects/](#appsprojects)
   - [apps/bidding/](#appsbidding)
   - [apps/payments/](#appspayments)
   - [apps/worklogs/](#appsworklogs)
   - [apps/messaging/](#appsmessaging)
   - [apps/notifications/](#appsnotifications)
   - [apps/search/](#appssearch)
5. [frontend/ — React Frontend](#frontend)
6. [deployment/ — Deployment](#deployment)
7. [requirements/ — Python Dependencies](#requirements)
8. [scripts/ — Helper Scripts](#scripts)
9. [docs/ — Documentation](#docs)
10. [logs/ — Application Logs](#logs)

---

## Root Directory

These files sit at the very top of the project. They control how the project starts, runs, tests, and deploys.

```
FreelanceFlow/
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── conftest.py
├── db.sqlite3
├── Dockerfile
├── docker-compose.yml
├── manage.py
├── Makefile
├── pytest.ini
├── README.md
├── setup.cfg
├── setup_new_features.sh
├── setup_new_features.bat
├── test_async_ai.py
├── vercel.json
├── folderstructure.md
├── apps/
├── config/
├── core/
├── deployment/
├── docs/
├── frontend/
├── logs/
├── requirements/
├── scripts/
└── venv/
```

---

### `.env`

**What it is:** The secret environment variables file. Contains database passwords, API keys, and other secrets.

**Why it exists:** You should never hardcode secrets in code. This file keeps them in one place and is ignored by Git.

**Key contents:** `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `GROQ_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `EMAIL_HOST_PASSWORD`, `GOOGLE_OAUTH_CLIENT_ID`, etc.

**Important:** This file is git-ignored. Never commit it. Use `.env.example` as a template.

---

### `.env.example`

**What it is:** A template showing all the environment variables the project needs, but with placeholder values.

**Why it exists:** New developers copy this file to `.env` and fill in their own values. It documents every variable the project uses.

**Key contents:** Sections for Django core, PostgreSQL (Supabase), Redis (Upstash), Celery, Razorpay, AWS S3, Groq (LLM), LangSmith (tracing), Elasticsearch, SMTP email, Sentry, Google OAuth, CORS, and platform config.

---

### `.gitignore`

**What it is:** Tells Git which files and folders to ignore (not track).

**Why it exists:** Prevents sensitive files (like `.env`), generated files (like `__pycache__`), and large folders (like `node_modules/`) from being committed to the repository.

**Key ignores:** `.env`, virtual envs, `__pycache__`, `db.sqlite3`, `node_modules/`, `frontend/dist/`, logs, `.DS_Store`, tooling caches.

---

### `.dockerignore`

**What it is:** Tells Docker which files to exclude when building Docker images.

**Why it exists:** Keeps Docker images small by excluding unnecessary files like `.env`, `venv/`, `__pycache__/`, and `*.pyc`.

---

### `manage.py`

**What it is:** The Django management command entry point. This is how you run the project.

**What it does:** Sets `DJANGO_SETTINGS_MODULE` to `config.settings.local` (local development) and calls `execute_from_command_line()`.

**How you use it:**
```bash
python manage.py runserver        # Start the dev server
python manage.py migrate          # Apply database migrations
python manage.py createsuperuser  # Create an admin user
python manage.py seed             # Seed demo data
python manage.py collectstatic    # Gather static files for production
```

---

### `conftest.py`

**What it is:** Shared pytest fixtures used across all test files.

**Why it exists:** Instead of creating test users and objects in every test file, you define them once here and reuse them everywhere.

**Key fixtures:** `client_user`, `freelancer_user`, `admin_user`, `project`, `bid`, `accepted_bid`, `contract`, `payment`, `escrowed_payment`, `worklog`, `conversation`, `message`, `notification`, plus authenticated DRF `APIClient` fixtures for each role.

---

### `pytest.ini`

**What it is:** Configuration file for the pytest test runner.

**What it does:** Tells pytest where to find tests (`apps/` directory), which Django settings to use (`config.settings.test`), and disables noisy warnings.

---

### `setup.cfg`

**What it is:** Configuration for Python linting and formatting tools.

**Key settings:** Sets flake8 max line length to 100 characters, excludes `venv/` and `__pycache__/`, and configures isort to use the `black` code style for consistent formatting.

---

### `Dockerfile`

**What it is:** Instructions for Docker to build the production image.

**How it works (2 stages):**
1. **Builder stage:** Installs Python dependencies and build tools into a virtual environment.
2. **Production stage:** Copies the venv, creates a non-root `appuser` for security, collects static files, and runs Gunicorn.

**Key detail:** Includes a health check — Docker will restart the container if the app stops responding.

---

### `docker-compose.yml`

**What it is:** Defines all the services (containers) the project needs to run.

**Services:**
| Service | Purpose |
|---------|---------|
| `redis` | Redis 7 — message broker for Celery + channel layer for WebSocket |
| `elastic` | Elasticsearch 8.14 — full-text search |
| `web` | Django dev server (HTTP API) |
| `daphne` | ASGI server for WebSocket (real-time chat) |
| `celery` | Background task worker (emails, PDFs, AI summaries) |
| `celery-beat` | Periodic task scheduler (digests, cleanup) |
| `flower` | Celery monitoring dashboard |

**How to use:** `docker compose up` starts infrastructure. `docker compose --profile app up` starts everything including app services.

---

### `vercel.json`

**What it is:** Deployment configuration for Vercel (hosts the React frontend).

**What it does:** Tells Vercel to run `npm install && npm run build` in the `frontend/` folder, output to `frontend/dist/`, and serve all routes as a single-page app (SPA rewrites).

---

### `test_async_ai.py`

**What it is:** A standalone demo script comparing sequential vs. concurrent async AI calls.

**What it shows:** Using `asyncio.gather()` to call multiple AI endpoints simultaneously gives ~5x speedup vs. calling them one after another. Run with `python test_async_ai.py`.

---

### `setup_new_features.sh`

**What it is:** Bash script to set up new features during development.

**What it does:** Checks for virtual environment, runs `makemigrations` and `migrate`, creates email templates directory, validates `.env` has required variables, and runs `collectstatic`.

---

### `setup_new_features.bat`

**What it is:** Windows batch equivalent of `setup_new_features.sh`. Same logic with Windows commands.

---

### `db.sqlite3`

**What it is:** The SQLite database file (local development only).

**Why it exists:** Django uses this for local development so you don't need to set up PostgreSQL locally. Contains all your local test data.

**Note:** This is git-ignored — each developer has their own.

---

## config

The `config/` folder contains all Django project configuration — settings, URL routing, ASGI/WSGI entry points, Celery setup, and more.

```
config/
├── __init__.py
├── asgi.py
├── celery.py
├── gunicorn_config.py
├── signals.py
├── urls.py
├── wsgi.py
└── settings/
    ├── __init__.py
    ├── base.py
    ├── local.py
    ├── production.py
    └── test.py
```

---

### `config/__init__.py`

**What it is:** Package init that imports and exports the `celery_app` instance.

**Why it matters:** When Django starts, it imports this file, which registers Celery so it can auto-discover background tasks from all apps.

---

### `config/settings/__init__.py`

**What it is:** Empty package init. Just makes `settings/` a Python package.

---

### `config/settings/base.py`

**What it is:** The main Django settings file. All other settings files inherit from this one.

**What it configures (this is the big one):**
- **INSTALLED_APPS:** Django core + DRF + Channels + Celery-Beat + Elasticsearch-DSL + Axes (brute-force protection)
- **Middleware:** Security, CORS, request logging, rate limiting
- **DRF:** JWT authentication (60min access, 7-day refresh with rotation), pagination (20/page), throttling, custom exception handler
- **Channels:** Redis channel layer for WebSocket support
- **Celery:** 3 queues (default, high-priority, low-priority), Redis broker with connection pooling
- **Razorpay:** Payment gateway integration
- **AWS S3:** Static/media file storage
- **Groq/LangSmith:** AI/LLM integration and tracing
- **Elasticsearch DSL:** Full-text search configuration
- **Email:** SMTP configuration
- **Redis Cache:** With Axes fallback for brute-force protection
- **Logging:** Rotating file handler (`logs/freelanceflow.log`), console output, per-app loggers

---

### `config/settings/local.py`

**What it is:** Local development overrides.

**Key differences from base:** `DEBUG=True`, allows `localhost` and `ngrok` hosts, uses console email backend (prints emails to terminal), disables SSL/secure cookies, disables Elasticsearch auto-sync (app works without ES running).

---

### `config/settings/production.py`

**What it is:** Production overrides for live deployment.

**Key differences:** `DEBUG=False`, full security headers (HSTS, XSS filter, nosniff, DENY frame), S3 storage for static/media files, JSON logging formatter, Sentry error tracking, PostgreSQL connection pooling with health checks.

---

### `config/settings/test.py`

**What it is:** Test overrides for running the test suite.

**Key differences:** Uses in-memory SQLite (fast), synchronous Celery (`CELERY_TASK_ALWAYS_EAGER` — tasks run immediately, no queue), MD5 password hasher (fast), in-memory email backend, silences all app loggers to `CRITICAL` level.

---

### `config/asgi.py`

**What it is:** ASGI entry point — handles both HTTP and WebSocket connections.

**What it does:** Wraps Django's ASGI app in `ProtocolTypeRouter` with WebSocket support via `AuthMiddlewareStack`. Registers signal handlers for graceful shutdown (flushes channel layer, closes DB/cache connections on SIGTERM/SIGINT).

---

### `config/wsgi.py`

**What it is:** Standard WSGI entry point — handles HTTP only (used by Gunicorn in production).

**What it does:** Calls `get_wsgi_application()` with the default settings module. Used when running with Gunicorn.

---

### `config/celery.py`

**What it is:** Celery application configuration for background tasks.

**What it configures:**
- Creates `Celery("freelanceflow")` app instance
- Autodiscovers tasks from all installed apps
- 3 queues with task routing: `payments` → high-priority, `pdfs/reports` → low-priority
- Worker settings: max tasks per worker, time limits, ack-late
- Redis connection pooling with keepalive
- Graceful shutdown handlers that close DB/cache connections

---

### `config/urls.py`

**What it is:** Root URL configuration — maps URLs to Django apps.

**URL routing:**
| URL Pattern | App |
|-------------|-----|
| `api/users/` | users app |
| `api/projects/` | projects app |
| `api/bidding/` | bidding app |
| `api/bids/` | bids alias |
| `api/contracts/` | contracts alias |
| `api/payments/` | payments app |
| `api/worklogs/` | worklogs app |
| `api/messaging/` | messaging app |
| `api/notifications/` | notifications app |
| `api/search/` | search app |
| `admin/` | Django admin |

In DEBUG mode, `/` redirects to the admin panel.

---

### `config/signals.py`

**What it is:** Graceful shutdown signal handler.

**What it does:** The `GracefulShutdown` class handles `SIGTERM` and `SIGINT` signals by closing database connections, cache connections, Elasticsearch connections, and flushing logs. This ensures clean shutdowns during deployments.

---

### `config/gunicorn_config.py`

**What it is:** Gunicorn (production HTTP server) configuration.

**Key settings:** Binds to `0.0.0.0:8000`, uses `gthread` worker class, configurable workers/threads via env vars, 120s timeout, 30s graceful timeout, max 1000 requests per worker before recycling, and lifecycle hooks with logging.

---

## core

The `core/` folder contains shared utilities used across all Django apps — caching, middleware, permissions, pagination, health checks, and more.

```
core/
├── __init__.py
├── cache.py
├── decorators.py
├── exceptions.py
├── health.py
├── middleware.py
├── middleware_shutdown.py
├── pagination.py
├── permissions.py
├── sanitizers.py
├── throttles.py
├── utils.py
└── management/
    └── commands/
        ├── seed.py
        ├── seed_clients1.py
        ├── seed_clients2.py
        ├── seed_clients3.py
        ├── seed_freelancers1.py
        ├── seed_freelancers2.py
        ├── seed_freelancers3.py
        ├── seed_projects1.py
        ├── seed_projects2.py
        └── seed_projects3.py
```

---

### `core/cache.py`

**What it is:** Redis caching utilities for performance optimization.

**Key classes:**
- `CacheKeys` — centralized cache key generation for projects, users, search, stats
- `CacheService` — wraps Django cache with `get_or_set`, `delete_pattern`, and invalidation methods
- `@cached` decorator — cache function results
- `@invalidate_on_save` signal decorator — auto-invalidate cache when models are saved

**Why it matters:** Caching avoids hitting the database for frequently accessed data (like project listings), making the app faster.

---

### `core/decorators.py`

**What it is:** Contains a single decorator `api_csrf_exempt` that wraps Django's `csrf_exempt` for token-authenticated API views.

**Why it matters:** API views using JWT tokens don't need CSRF protection, but you still want to be explicit about disabling it.

---

### `core/exceptions.py`

**What it is:** Custom DRF exception handler and business error classes.

**What it does:** The `custom_exception_handler` returns a consistent `{error, code, field}` JSON format for all errors. Business error classes (`BusinessError`, `PermissionDeniedError`, `NotFoundError`, `ValidationError`) let service-layer code raise meaningful errors that get formatted properly.

---

### `core/health.py`

**What it is:** Health check endpoints for monitoring.

**What it provides:**
- `health_check` — tests DB, Redis, Celery (ping workers), and Elasticsearch. Returns `{status, checks}` JSON.
- `readiness_check` — verifies DB connectivity (is the app ready to serve traffic?)
- `liveness_check` — confirms the process is alive (should Docker/Kubernetes restart it?)

**Registered at:** `/health/`

---

### `core/middleware.py`

**What it is:** Custom middleware classes that run on every request.

**Key middleware:**
- `RequestLoggingMiddleware` — logs method, path, status code, duration, and IP for every request
- `SecurityHeadersMiddleware` — adds `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy` headers
- `RateLimitMiddleware` — Redis-based rate limiting (100/hr anonymous, 1000/hr authenticated)
- `CacheControlMiddleware` — sets no-cache headers for API/admin paths
- `CORSCustomMiddleware` — adds CORS headers based on request origin

---

### `core/middleware_shutdown.py`

**What it is:** `GracefulShutdownMiddleware` — returns 503 for all new requests during graceful shutdown.

**Why it matters:** During deployments, you want to stop accepting new requests but finish processing current ones. This middleware checks if the app is shutting down and rejects new requests cleanly.

---

### `core/pagination.py`

**What it is:** `StandardResultsPagination` — DRF pagination class.

**Key settings:** 20 items per page (default), configurable via `?page_size=` query parameter (max 100). Returns standard `{count, next, previous, results}` format.

---

### `core/permissions.py`

**What it is:** DRF permission classes for access control.

**Key classes:**
- `IsOwnerOrAdmin` — user is the object owner or staff
- `BaseRolePermission` — abstract class for role-based permissions
- `IsClient` — user has CLIENT role
- `IsFreelancer` — user has FREELANCER role
- `IsOwner` — `obj.user == request.user`

---

### `core/sanitizers.py`

**What it is:** XSS (Cross-Site Scripting) protection utilities.

**Key functions:**
- `sanitize_html` — escapes HTML or allows basic formatting tags
- `sanitize_text_field` — escapes all HTML
- `strip_dangerous_content` — removes `<script>`, `<iframe>`, `on*` event handlers, and `javascript:` protocol

**Why it matters:** Prevents users from injecting malicious scripts into the platform.

---

### `core/throttles.py`

**What it is:** Custom rate-limiting throttle classes.

**Key classes:**
- `TieredRateThrottle` — applies different rates based on subscription tier (FREE: 30/min, PRO: 300/min)
- `LoginRateThrottle` — enforces 5 login attempts per minute

---

### `core/utils.py`

**What it is:** Shared utility functions.

**Key functions:**
- `calculate_platform_cut` — calculates platform fee and freelancer amount using `Decimal` (avoids floating-point errors)
- `generate_report_id` — generates a unique UUID for reports
- `format_currency` — formats amounts as currency strings
- `truncate_text` — truncates long text with `...` suffix

---

### `core/management/commands/seed.py`

**What it is:** Management command to populate the database with demo data.

**What it creates:** 2 clients, 2 freelancers, 5 projects, 4 bids, 1 contract, and a conversation with 5 messages.

**How to use:** `python manage.py seed`

**Key detail:** Disconnects Elasticsearch signals during seeding (to avoid indexing errors), reconnects after. Prints login credentials to console.

---

### `core/management/commands/seed_clients1.py` / `seed_clients2.py` / `seed_clients3.py`

**What it is:** Management commands to seed frontend-focused, backend-focused, and full-stack clients.

**How to use:** `python manage.py seed_clients1`

**Key detail:** Skips if email already exists (idempotent — safe to run multiple times).

---

### `core/management/commands/seed_freelancers1.py` / `seed_freelancers2.py` / `seed_freelancers3.py`

**What it is:** Management commands to seed freelancers with different specializations.

**What they create:** Freelancers with detailed bios, skills, hourly rates, subscription tiers, and ratings.

---

### `core/management/commands/seed_projects1.py` / `seed_projects2.py` / `seed_projects3.py`

**What it is:** Management commands to seed projects with bids from freelancers.

**What they create:** OPEN projects with multiple bids, notifications for each bid.

---

## apps

The `apps/` folder contains all Django applications. Each app handles one domain of the platform. Every app follows the same structure: `models/`, `serializers/`, `services/`, `views/`, `urls/`, `tests/`, `selectors.py`, `permissions.py`, `logger.py`.

```
apps/
├── __init__.py
├── users/
├── projects/
├── bidding/
├── payments/
├── worklogs/
├── messaging/
├── notifications/
└── search/
```

---

## apps/users

The users app handles authentication, profiles, JWT tokens, Google OAuth2 Single Sign-On, activity logging, and online status.

```
apps/users/
├── __init__.py
├── admin.py
├── apps.py
├── logger.py
├── permissions.py
├── selectors.py
├── signals.py
├── tasks.py
├── tokens.py
├── models/
│   ├── __init__.py
│   ├── models.py
│   └── models_extended.py
├── serializers/
│   ├── __init__.py
│   ├── serializers.py
│   └── serializers_extended.py
├── services/
│   ├── __init__.py
│   ├── services.py
│   ├── services_activity.py
│   └── services_status.py
├── urls/
│   ├── __init__.py
│   ├── urls.py
│   └── urls_extended.py
├── views/
│   ├── __init__.py
│   ├── views.py
│   ├── views_extended.py
│   └── views_google_oauth.py
└── tests/
    ├── __init__.py
    ├── factories.py
    ├── test_models.py
    ├── test_selectors.py
    ├── test_services.py
    └── test_views.py
```


---

### `apps/users/admin.py`

**What it is:** Django admin configuration for User model.

**What it does:** Registers `User` with `UserAdmin` (adds role fieldset, search, filters). Shows `FreelancerProfileInline` or `ClientProfileInline` based on user role.

---

### `apps/users/apps.py`

**What it is:** `UsersConfig` AppConfig.

**What it does:** Imports signals in `ready()` to register post-save handlers (auto-create profile on user creation).

---

### `apps/users/logger.py`

**What it is:** Structured logging helpers for the users app.

**Key functions:** `log_user_created`, `log_user_login`, `log_user_login_failed`, `log_profile_updated`, `log_password_changed`.

---

### `apps/users/permissions.py`

**What it is:** DRF permission classes specific to users.

**Key classes:** `IsFreelancer`, `IsClient`, `IsOwner` (checks `obj.user`), `IsSelf` (checks `obj == request.user`).

---

### `apps/users/selectors.py`

**What it is:** Database query functions (read operations only).

**Key functions:** `get_user_by_id`, `get_user_by_email`, `get_freelancer_profile`, `get_client_profile`, `list_freelancers` (with optional skill filtering), `list_clients`.

**Pattern:** Selectors are pure query functions — no business logic, just clean database reads.

---

### `apps/users/signals.py`

**What it is:** Django signals that run when a User is saved.

**What it does:**
- `create_user_profile` — auto-creates `FreelancerProfile` or `ClientProfile` when a user is created, then sends welcome email via Celery
- `save_user_profile` — keeps profile in sync with user saves

---

### `apps/users/tasks.py`

**What it is:** Celery background tasks for the users app.

**Key task:** `send_welcome_email_task` — sends a role-appropriate welcome email asynchronously.

---

### `apps/users/tokens.py`

**What it is:** Token generators for email verification and password reset.

**Key classes:**
- `AccountActivationTokenGenerator` — hashes `pk + timestamp + is_active` for email verification links
- `password_reset_token` — Django's built-in password reset token

---

### `apps/users/models/models.py`

**What it is:** Core user and profile models.

**Key models:**
- `UserManager` — email-based user creation and superuser creation
- `User` — extends `AbstractUser`, email as `USERNAME_FIELD`, CLIENT/FREELANCER role choices, soft-deactivation fields
- `FreelancerProfile` — OneToOne with User. Fields: bio, skills (JSONField), hourly_rate, subscription_tier (FREE/PRO), total_earned, avatar, is_available, average_rating, total_reviews, razorpay_fund_account_id
- `ClientProfile` — OneToOne with User. Fields: company_name, total_spent, avatar, average_rating, total_reviews

---

### `apps/users/models/models_extended.py`

**What it is:** Extended models for 2FA, activity logging, and online status.

**Key models:**
- `TwoFactorAuth` — OneToOne with User. Fields: is_enabled, TOTP secret_key, backup_codes (JSON)
- `ActivityLog` — audit log with ActionType choices (LOGIN, BID_PLACED, PAYMENT_MADE, etc.), ip_address, user_agent, metadata (JSON)
- `UserOnlineStatus` — OneToOne with User. Fields: is_online, last_seen

---

### `apps/users/serializers/serializers.py`

**What it is:** DRF serializers for user data validation and transformation.

**Key serializers:**
- `UserRegistrationSerializer` — handles registration with password confirmation and validation
- `UserSerializer` — returns user data with nested profiles
- `UserProfileUpdateSerializer` — handles updating both role-specific profiles
- `ChangePasswordSerializer`, `PasswordResetRequestSerializer`, `PasswordResetConfirmSerializer`
- `EmailVerificationSerializer`, `AvatarUploadSerializer`, `AvailabilityToggleSerializer`
- `AccountDeactivationSerializer` — requires typing "DEACTIVATE" to confirm

---

### `apps/users/serializers/serializers_extended.py`

**What it is:** Extended serializers for 2FA, activity logs, and online status.

**Key serializers:** `Enable2FASerializer`, `Verify2FASerializer`, `Disable2FASerializer`, `ActivityLogSerializer`, `UserOnlineStatusSerializer`.

---

### `apps/users/services/services.py`

**What it is:** Core business logic for user operations.

**Key functions:**
- `create_user` — validates email/password/role, creates user atomically
- `update_profile` — updates user + role-specific profile fields
- `change_password` — validates old password, sets new one
- `send_password_reset_email` — generates token + link, sends email
- `reset_password` — validates token, sets new password
- `send_verification_email`, `verify_email`
- `update_avatar`, `toggle_freelancer_availability`
- `deactivate_account` — soft delete with confirmation email
- `reactivate_account`

---

### `apps/users/services/services_activity.py`

**What it is:** Activity logging services for audit trails.

**Key functions:** `log_activity`, `get_user_activity_log` (filtered by action/resource_type), `get_recent_logins`, `get_security_events`, `get_payment_activities`, `get_activity_summary` (aggregate counts).

---

### `apps/users/services/services_status.py`

**What it is:** Online status tracking services.

**Key functions:** `set_user_online`, `set_user_offline`, `update_last_seen`, `get_user_status`, `is_user_online` (auto-marks offline after 5min), `get_online_users`, `get_online_count`, `set_status_message`, `cleanup_stale_online_status` (marks offline after 10min inactivity).

---

### `apps/users/urls/urls.py`

**What it is:** URL patterns for core user endpoints.

**Endpoints:** `register/`, `login/`, `token/`, `token/refresh/`, `me/`, `change-password/`, `avatar/`, `availability/`, `password-reset/`, `verify-email/`, `deactivate/`, `reactivate/`, `<int:pk>/`.

---

### `apps/users/urls/urls_extended.py`

**What it is:** URL patterns for extended user features and OAuth.

**Endpoints:** `auth/google/`, `auth/google/callback/`, `activity/`, `status/` for Google OAuth2 SSO flow, activity logs, and online status.

---

### `apps/users/views/views.py`

**What it is:** API views for core user operations.

**Key views:**
- `RegisterView` — POST, throttled, calls `create_user` service
- `LoginView` — extends DRF's `TokenObtainPairView` (JWT)
- `ProfileView` — GET/PATCH `/me/`
- `ChangePasswordView`, `UserDetailView`, `PasswordResetRequestView`, `PasswordResetConfirmView`
- `EmailVerificationView`, `UpdateAvatarView`, `ToggleAvailabilityView`, `DeactivateAccountView`

---

### `apps/users/views/views_extended.py`

**What it is:** API ViewSets for extended features.

**Key ViewSets:** `ActivityLogViewSet` (list/security/summary), `OnlineStatusViewSet` (me/message/online/count).

---

### `apps/users/views/views_google_oauth.py`

**What it is:** Google OAuth2 Authentication views.

**Key views:**
- `GoogleOAuthInitView` — GET `/api/users/auth/google/`, returns Google authorization URL, throttled (`OAuthRateThrottle`: 10/min).
- `GoogleOAuthCallbackView` — GET `/api/users/auth/google/callback/`, exchanges code for Google tokens, creates/gets User, issues JWT tokens & redirects browser to frontend.

---

### `apps/users/tests/factories.py`

**What it is:** Test helper functions for creating test data.

**Key functions:** `make_freelancer` and `make_client` — create User instances with proper profiles. Uses `create_user` for proper password hashing.

---

## apps/projects

The projects app handles project CRUD, categories, bookmarks, drafts, and sharing.

```
apps/projects/
├── __init__.py
├── admin.py
├── apps.py
├── logger.py
├── permissions.py
├── selectors.py
├── models/
│   ├── __init__.py
│   ├── models.py
│   └── models_extended.py
├── serializers/
│   ├── __init__.py
│   ├── serializers.py
│   └── serializers_extended.py
├── services/
│   ├── __init__.py
│   ├── services.py
│   ├── services_bookmark.py
│   ├── services_category.py
│   ├── services_draft.py
│   └── services_share.py
├── urls/
│   ├── __init__.py
│   ├── urls.py
│   └── urls_extended.py
├── views/
│   ├── __init__.py
│   ├── views.py
│   └── views_extended.py
└── tests/
    ├── __init__.py
    ├── factories.py
    ├── test_models.py
    ├── test_services.py
    └── test_views.py
```

---

### `apps/projects/permissions.py`

**What it is:** Project-specific permission classes.

**Key classes:** `IsProjectOwner` (client == request.user), `IsProjectClient`, `IsOpenProject` (status == OPEN).

---

### `apps/projects/selectors.py`

**What it is:** Database query functions for projects.

**Key functions:** `get_project_by_id`, `get_open_projects` (with budget/skills/search filtering), `get_client_projects`, `get_project_skills`.

---

### `apps/projects/models/models.py`

**What it is:** Core project models.

**Key models:**
- `Project` — statuses: OPEN/IN_PROGRESS/COMPLETED/CANCELLED. Fields: client (FK), title, description, budget, deadline
- `ProjectSkill` — skill_name (unique per project)

---

### `apps/projects/models/models_extended.py`

**What it is:** Extended project models.

**Key models:**
- `ProjectCategory` — name, slug, icon (for organizing projects)
- `ProjectBookmark` — user + project (unique — one bookmark per user per project)
- `ProjectDraft` — unsaved project drafts with JSON skills
- `ProjectShare` — token-based public links with view_count and expiry

---

### `apps/projects/services/services.py`

**What it is:** Core project CRUD services.

**Key functions:**
- `create_project` — validates role/title/budget, creates with skills
- `update_project` — owner-only, OPEN status only
- `close_project` — cancels the project
- `mark_project_in_progress`, `mark_project_completed`

---

### `apps/projects/services/services_bookmark.py`

**What it is:** Bookmark services.

**Key functions:** `bookmark_project`, `remove_bookmark`, `get_bookmarked_projects`, `is_bookmarked`.

---

### `apps/projects/services/services_category.py`

**What it is:** Category CRUD services.

**Key functions:** `create_category`, `get_all_categories`, `get_category_by_slug`.

---

### `apps/projects/services/services_draft.py`

**What it is:** Draft services for saving incomplete projects.

**Key functions:** `save_draft`, `update_draft`, `get_user_drafts`, `publish_draft` (converts draft to a live Project).

---

### `apps/projects/services/services_share.py`

**What it is:** Share link services for public project links.

**Key functions:** `generate_share_link` (uses `secrets.token_urlsafe`), `get_project_by_token` (validates expiry, increments view_count), `deactivate_share_link`.

---

### `apps/projects/views/views.py`

**What it is:** `ProjectViewSet` — full CRUD with role-based querysets.

**Behavior:** Clients see their own projects. Freelancers see open projects with filters. Custom action: `my_projects`.

---

### `apps/projects/views/views_extended.py`

**What it is:** `ProjectBookmarkViewSet` — bookmark/unbookmark projects, list bookmarks, check status.

---

## apps/bidding

The bidding app handles bids, contracts, reviews, amendments, counter-offers, and contract terminations. This is the most complex app.

```
apps/bidding/
├── __init__.py
├── admin.py
├── apps.py
├── logger.py
├── permissions.py
├── selectors.py
├── models/
│   ├── __init__.py
│   ├── models.py
│   ├── models_amendment.py
│   ├── models_extended.py
│   ├── models_review.py
│   └── models_termination.py
├── serializers/
│   ├── __init__.py
│   ├── serializers.py
│   ├── serializers_extended.py
│   └── serializers_review.py
├── services/
│   ├── __init__.py
│   ├── services.py
│   ├── services_amendment.py
│   ├── services_counter_offer.py
│   ├── services_retraction.py
│   ├── services_review.py
│   ├── services_termination.py
│   └── services_worklog_approval.py
├── urls/
│   ├── __init__.py
│   ├── bids_only.py
│   ├── contracts_only.py
│   ├── urls.py
│   ├── urls_extended.py
│   └── urls_review.py
├── views/
│   ├── __init__.py
│   ├── views.py
│   ├── views_extended.py
│   └── views_review.py
└── tests/
    ├── __init__.py
    ├── test_services.py
    └── test_views.py
```

---

### `apps/bidding/permissions.py`

**What it is:** Bidding-specific permission classes.

**Key classes:** `IsBidOwner`, `IsProjectClient`, `IsContractParticipant`.

---

### `apps/bidding/models/models.py`

**What it is:** Core bidding models.

**Key models:**
- `Bid` — statuses: PENDING/ACCEPTED/REJECTED/WITHDRAWN. Fields: project (FK), freelancer (FK), amount, cover_letter. Unique constraint: one bid per freelancer per project.
- `Contract` — OneToOne with Bid. Fields: agreed_amount, start_date, end_date, is_active. Properties: project, freelancer, client.

---

### `apps/bidding/models/models_extended.py`

**What it is:** Extended bidding models.

**Key models:**
- `BidRetraction` — OneToOne with Bid. Fields: reason, retracted_at
- `CounterOffer` — Fields: bid (FK), client (FK), proposed_amount, proposed_deadline, message, status (PENDING/ACCEPTED/REJECTED/EXPIRED), expires_at
- `WorklogApproval` — OneToOne with WorkLog. Fields: client (FK), status (PENDING/APPROVED/REJECTED), feedback

---

### `apps/bidding/models/models_amendment.py`

**What it is:** Contract amendment model for tracking scope/budget/deadline changes.

**Key model:** `ContractAmendment` — statuses: PENDING/APPROVED/REJECTED. Stores proposed changes, reason, approval metadata.

---

### `apps/bidding/models/models_review.py`

**What it is:** Review and rating models.

**Key models:**
- `Review` — rating (1-5) with sub-ratings (communication, quality, professionalism). Supports both client and freelancer reviewers.
- `ReviewResponse` — OneToOne reply to a review.

---

### `apps/bidding/models/models_termination.py`

**What it is:** Contract termination request model.

**Key model:** `ContractTerminationRequest` — requires other party approval. Stores reason, explanation, refund_percentage, approval/rejection metadata.

---

### `apps/bidding/services/services.py`

**What it is:** Core bid and contract services.

**Key functions:**
- `submit_bid` — validates freelancer role, project open, no duplicate, amount, cover letter length
- `accept_bid` — uses `select_for_update` (row locking), rejects other bids, creates contract, marks project in-progress, dispatches notification
- `reject_bid`, `withdraw_bid`, `complete_contract`

---

### `apps/bidding/services/services_amendment.py`

**What it is:** Contract amendment services.

**Key functions:** `propose_contract_amendment`, `approve_contract_amendment` (applies budget/scope/deadline changes), `reject_contract_amendment`, `get_contract_amendments`.

---

### `apps/bidding/services/services_counter_offer.py`

**What it is:** Counter-offer services (client proposes new amount/timeline).

**Key functions:** `create_counter_offer`, `accept_counter_offer` (updates bid amount), `reject_counter_offer`, `get_counter_offers_for_bid`, `get_pending_counter_offers`, `get_counter_offer_stats`.

---

### `apps/bidding/services/services_retraction.py`

**What it is:** Bid retraction services.

**Key functions:** `retract_bid`, `can_retract_bid`, `get_retracted_bids`, `get_retraction_details`.

---

### `apps/bidding/services/services_review.py`

**What it is:** Review and rating services.

**Key functions:**
- `create_review` — validates contract completed, prevents duplicates, updates user rating
- `update_review`, `delete_review`
- `create_review_response`
- `get_user_reviews`, `get_user_rating_summary` (aggregated stats with breakdown)
- `_update_user_rating` — recalculates and caches rating on profile

---

### `apps/bidding/services/services_termination.py`

**What it is:** Contract termination services.

**Key functions:** `request_contract_termination`, `approve_contract_termination` (handles refund percentage, calls payment processing), `reject_contract_termination`, `force_terminate_contract` (admin-only).

---

### `apps/bidding/services/services_worklog_approval.py`

**What it is:** Worklog approval services.

**Key functions:** `submit_worklog_for_approval`, `approve_worklog`, `reject_worklog` (requires feedback), `get_pending_approvals`, `get_worklog_approval_status`, `get_approval_stats`.

---

### `apps/bidding/urls/bids_only.py`

**What it is:** Short-form alias routes: `/api/bids/*` → `/api/bidding/bids/*`.

**Why it exists:** Provides a shorter, cleaner URL for bid operations.

---

### `apps/bidding/urls/contracts_only.py`

**What it is:** Short-form alias routes: `/api/contracts/*` → `/api/bidding/contracts/*`.

---

### `apps/bidding/views/views.py`

**What it is:** Core bid and contract API views.

**Key ViewSets:**
- `BidViewSet` — CRUD with role-based queries. Custom actions: `accept`, `reject`, `my_bids`
- `ContractViewSet` — read-only contract listing/detail

---

### `apps/bidding/views/views_extended.py`

**What it is:** Extended ViewSets for worklog approvals, retractions, counter-offers.

**Key ViewSets:** `WorklogApprovalViewSet`, `BidRetractionViewSet`, `CounterOfferViewSet`.

---

### `apps/bidding/views/views_review.py`

**What it is:** Review-specific ViewSet.

**Key actions:** `respond` (reply to review), `received`/`given` (list reviews by direction), `user/<id>`/`user/<id>/summary` (user-specific reviews and stats).

---

## apps/payments

The payments app handles Razorpay escrow payments, releases, refunds, milestones, invoices, tax documents, and multi-currency support.

```
apps/payments/
├── __init__.py
├── admin.py
├── apps.py
├── logger.py
├── permissions.py
├── selectors.py
├── tasks.py
├── models/
│   ├── __init__.py
│   ├── models.py
│   ├── models_dispute.py
│   ├── models_extended.py
│   └── models_milestone.py
├── serializers/
│   ├── __init__.py
│   ├── serializers.py
│   └── serializers_extended.py
├── services/
│   ├── __init__.py
│   ├── services.py
│   ├── services_currency.py
│   ├── services_invoice.py
│   ├── services_milestone.py
│   └── services_tax.py
├── urls/
│   ├── __init__.py
│   ├── urls.py
│   └── urls_extended.py
├── views/
│   ├── __init__.py
│   ├── views.py
│   └── views_extended.py
└── tests/
    ├── __init__.py
    ├── test_services.py
    ├── test_views.py
    └── test_webhook.py
```

---

### `apps/payments/tasks.py`

**What it is:** Celery background tasks for payment processing.

**What it handles:** Razorpay webhook processing, payouts to freelancers, refund processing — all run asynchronously.

---

### `apps/payments/models/models.py`

**What it is:** Core payment models.

**Key models:**
- `Payment` — statuses: PENDING/ESCROWED/PAYOUT_PENDING/RELEASED/PAYOUT_FAILED/REFUNDED. Fields: Razorpay order/payment/payout/refund IDs, refund_amount
- `Escrow` — OneToOne with Payment. Fields: held_amount, refund_amount, released_at
- `PlatformEarning` — cut_percentage, cut_amount (tracks platform revenue)
- `PaymentEvent` — idempotency for Razorpay webhooks (prevents duplicate processing)

---

### `apps/payments/models/models_dispute.py`

**What it is:** Payment dispute model.

**Key model:** `PaymentDispute` — statuses: OPEN/UNDER_REVIEW/RESOLVED/CLOSED. Resolution choices: FAVOR_CLIENT/FAVOR_FREELANCER/SPLIT/REFUND. Includes `DisputeMessage` for threaded dispute communication.

---

### `apps/payments/models/models_extended.py`

**What it is:** Extended payment models.

**Key models:**
- `TaxDocument` — 1099/W-9 forms per freelancer+year
- `CurrencyExchangeRate` — from/to currency, rate
- `MultiCurrencyPayment` — original/converted amounts, exchange rate

---

### `apps/payments/models/models_milestone.py`

**What it is:** Milestone payment model for staged payments.

**Key model:** `PaymentMilestone` — statuses: PENDING/IN_PROGRESS/SUBMITTED/APPROVED/PAID/REJECTED. Fields: percentage-based amounts, deliverable tracking, due dates, client feedback.

---

### `apps/payments/services/services.py`

**What it is:** Core payment services.

**Key functions:** Create escrow, process Razorpay webhooks, release payments to freelancers, handle refunds. Uses Razorpay API for all payment operations.

---

### `apps/payments/services/services_currency.py`

**What it is:** Currency conversion services for multi-currency support.

---

### `apps/payments/services/services_invoice.py`

**What it is:** Invoice generation services.

---

### `apps/payments/services/services_milestone.py`

**What it is:** Milestone payment services.

**Key functions:** Create, approve, and pay milestones.

---

### `apps/payments/services/services_tax.py`

**What it is:** Tax document generation services for freelancer tax forms.

---

### `apps/payments/tests/test_webhook.py`

**What it is:** Tests for Razorpay webhook processing.

**Why it matters:** Webhook handling is critical — payment confirmation must be reliable. These tests verify idempotency, signature validation, and correct state transitions.

---

## apps/worklogs

The worklogs app handles daily work logs, weekly reports, AI-powered summaries, PDF generation, deliverables, and time-off tracking.

```
apps/worklogs/
├── __init__.py
├── admin.py
├── apps.py
├── logger.py
├── permissions.py
├── selectors.py
├── tasks.py
├── models/
│   ├── __init__.py
│   ├── models.py
│   └── models_extended.py
├── serializers/
│   ├── __init__.py
│   └── serializers.py
├── services/
│   ├── __init__.py
│   ├── ai_service.py
│   ├── groq_service.py
│   ├── pdf_service.py
│   ├── services.py
│   └── services_timeoff.py
├── templates/
│   └── worklogs/
│       ├── delivery_proof.html
│       └── weekly_report.html
├── urls/
│   ├── __init__.py
│   └── urls.py
├── views/
│   ├── __init__.py
│   └── views.py
└── tests/
    ├── __init__.py
    ├── test_ai_service.py
    ├── test_models.py
    ├── test_pdf_service.py
    ├── test_services.py
    └── test_views.py
```

---

### `apps/worklogs/tasks.py`

**What it is:** Celery background tasks for worklogs.

**What it handles:** PDF generation (delivery proofs, weekly reports), AI report generation, weekly report generation — all run asynchronously.

---

### `apps/worklogs/models/models.py`

**What it is:** Core worklog models.

**Key models:**
- `WorkLog` — statuses: DRAFT/PENDING_APPROVAL/APPROVED/REJECTED. Fields: contract, freelancer, date, description, hours_worked, screenshot, reference_url, ai_generated_summary, client_notes, approval metadata
- `WeeklyReport` — AI-generated reports. Fields: contract, week range, ai_summary, pdf_url, sent_to_client_at
- `Deliverable` — AI chat transcript, generated report, attached files, revision workflow, payment_released flag
- `DeliveryProof` — final PDF with tamper-evident report_id, total_hours/logs/deliverables counts

---

### `apps/worklogs/models/models_extended.py`

**What it is:** Time-off tracking model.

**Key model:** `TimeOff` — types: VACATION/SICK/PERSONAL/OTHER. Statuses: PENDING/APPROVED/REJECTED. Fields: contract (optional), date range, reason.

---

### `apps/worklogs/services/ai_service.py`

**What it is:** AI service for generating work summaries from chat transcripts.

**What it does:** Takes a conversation between freelancer and AI, generates a structured work summary. Uses Groq LLM for fast inference.

---

### `apps/worklogs/services/groq_service.py`

**What it is:** Groq API integration for AI chat completions.

**What it does:** Wraps the Groq API (fast LLM inference) for generating AI responses in work summary conversations.

---

### `apps/worklogs/services/pdf_service.py`

**What it is:** PDF generation service using WeasyPrint.

**What it does:** Converts HTML templates (`delivery_proof.html`, `weekly_report.html`) into PDF files for delivery proofs and weekly reports.

---

### `apps/worklogs/services/services.py`

**What it is:** Core worklog services.

**Key functions:** Create/update/submit/approve worklogs, generate weekly reports, create deliverables.

---

### `apps/worklogs/services/services_timeoff.py`

**What it is:** Time-off request services.

**Key functions:** Submit, approve, reject, and list time-off requests.

---

### `apps/worklogs/templates/worklogs/delivery_proof.html`

**What it is:** HTML template for delivery proof PDF generation.

**Why it exists:** WeasyPrint converts this HTML to PDF. The template includes styling for a professional-looking delivery document.

---

### `apps/worklogs/templates/worklogs/weekly_report.html`

**What it is:** HTML template for weekly report PDF generation.

---

## apps/messaging

The messaging app handles real-time WebSocket chat between clients and freelancers.

```
apps/messaging/
├── __init__.py
├── admin.py
├── apps.py
├── consumers.py
├── logger.py
├── permissions.py
├── routing.py
├── selectors.py
├── models/
│   ├── __init__.py
│   ├── models.py
│   └── models_extended.py
├── serializers/
│   ├── __init__.py
│   └── serializers.py
├── services/
│   ├── __init__.py
│   ├── services.py
│   ├── services_search.py
│   └── services_typing.py
├── urls/
│   ├── __init__.py
│   └── urls.py
├── views/
│   ├── __init__.py
│   └── views.py
└── tests/
    ├── __init__.py
    ├── test_consumers.py
    └── test_views.py
```

---

### `apps/messaging/consumers.py`

**What it is:** `ChatConsumer` — async WebSocket consumer for real-time contract chat.

**Key features:**
- JWT authentication via `?token=` query parameter
- Authorization limited to contract participants (client + freelancer only)
- Message persistence via `database_sync_to_async` (avoids blocking the event loop)
- Read receipts (auto-mark on receive, client-initiated flush)
- Room group broadcasting via Redis channel layer

**Why it matters:** This is the core of real-time communication. It uses Django Channels to handle WebSocket connections asynchronously.

---

### `apps/messaging/routing.py`

**What it is:** WebSocket URL routing for chat consumers.

**What it does:** Maps WebSocket URLs (like `ws/chat/<room_name>/`) to the `ChatConsumer`.

---

### `apps/messaging/models/models.py`

**What it is:** Core messaging models.

**Key models:**
- `Conversation` — OneToOne with Contract (each contract has one conversation). Auto timestamps.
- `Message` — Fields: conversation (FK), sender (FK), content, attachments (JSON), is_read flag. Ordered by `created_at`.

---

### `apps/messaging/models/models_extended.py`

**What it is:** Extended messaging models (typing indicators, message reactions).

---

### `apps/messaging/services/services.py`

**What it is:** Core messaging services.

**Key functions:** `get_or_create_conversation`, `send_message`, `mark_messages_as_read_returning_ids` (returns IDs for broadcast), `get_conversation_messages`.

---

### `apps/messaging/services/services_search.py`

**What it is:** Message search services.

---

### `apps/messaging/services/services_typing.py`

**What it is:** Typing indicator services (Redis-based presence tracking).

---

### `apps/messaging/tests/test_consumers.py`

**What it is:** Tests for WebSocket consumer behavior.

**What it tests:** Connection authentication, message sending/receiving, read receipts, authorization (non-participants blocked).

---

## apps/notifications

The notifications app handles in-app, email, and push notifications, plus email digests and platform announcements.

```
apps/notifications/
├── __init__.py
├── admin.py
├── apps.py
├── logger.py
├── permissions.py
├── selectors.py
├── tasks.py
├── models/
│   ├── __init__.py
│   ├── models.py
│   ├── models_extended.py
│   └── models_push.py
├── serializers/
│   ├── __init__.py
│   └── serializers.py
├── services/
│   ├── __init__.py
│   ├── email_service.py
│   ├── services.py
│   ├── services_announcement.py
│   ├── services_digest.py
│   └── services_push.py
├── urls/
│   ├── __init__.py
│   └── urls.py
├── views/
│   ├── __init__.py
│   └── views.py
└── tests/
    ├── __init__.py
    └── test_services.py
```

---

### `apps/notifications/tasks.py`

**What it is:** Celery background tasks for async notification delivery.

**What it handles:** Sending email notifications, push notifications, and compiling email digests — all run asynchronously.

---

### `apps/notifications/models/models.py`

**What it is:** Core notification model.

**Key model:** `Notification` — types: BID_SUBMITTED/BID_ACCEPTED/ESCROW_CREATED/LOG_SUBMITTED/REPORT_READY/PAYMENT_RELEASED/PROOF_READY/MESSAGE_RECEIVED. Fields: recipient (FK), title, body, is_read flag. Indexed on recipient+is_read for fast queries.

---

### `apps/notifications/models/models_extended.py`

**What it is:** Extended notification models (push notifications, email queue, announcements).

---

### `apps/notifications/models/models_push.py`

**What it is:** Push notification model for FCM/APNs integration.

---

### `apps/notifications/services/services.py`

**What it is:** Core notification service.

**Key functions:** `create_notification`, `get_user_notifications`, `mark_as_read`, `mark_all_read`, `get_unread_count`.

---

### `apps/notifications/services/email_service.py`

**What it is:** Email notification service (SMTP-based).

---

### `apps/notifications/services/services_announcement.py`

**What it is:** Platform-wide announcement services (broadcast messages to all users).

---

### `apps/notifications/services/services_digest.py`

**What it is:** Email digest services — batches multiple notifications into a single periodic email.

---

### `apps/notifications/services/services_push.py`

**What it is:** Push notification delivery services (FCM integration).

---

## apps/search

The search app handles Elasticsearch integration, autocomplete, search history, and saved searches.

```
apps/search/
├── __init__.py
├── admin.py
├── apps.py
├── documents.py
├── logger.py
├── permissions.py
├── selectors.py
├── signals.py
├── models/
│   ├── __init__.py
│   └── models_extended.py
├── serializers/
│   ├── __init__.py
│   └── serializers.py
├── services/
│   ├── __init__.py
│   ├── services.py
│   ├── services_autocomplete.py
│   ├── services_history.py
│   └── services_saved.py
├── urls/
│   ├── __init__.py
│   └── urls.py
├── views/
│   ├── __init__.py
│   └── views.py
└── tests/
    ├── __init__.py
    └── test_views.py
```

---

### `apps/search/documents.py`

**What it is:** Elasticsearch DSL document definitions.

**Key documents:**
- `ProjectDocument` — indexes Project with client_name, skills, status, budget, deadline
- `FreelancerDocument` — indexes FreelancerProfile with email, full_name, skills, hourly_rate, tier

**Why it exists:** These define how data is indexed in Elasticsearch for fast full-text search.

---

### `apps/search/signals.py`

**What it is:** Django signal handlers that sync Elasticsearch indices on model changes.

**What it does:** When a Project or FreelancerProfile is saved/deleted, the corresponding ES document is updated/deleted. All handlers catch `ConnectionError` defensively — the app works without ES running. Checks `ELASTICSEARCH_DSL_AUTOSYNC` flag before attempting updates.

---

### `apps/search/models/models_extended.py`

**What it is:** Extended search models.

**Key models:**
- `SearchHistory` — logs user searches (query, search_type, filters, results_count)
- `SavedSearch` — user-saved search queries with filters
- `SearchSuggestion` — autocomplete terms with popularity scores

---

### `apps/search/services/services.py`

**What it is:** Core search services (Elasticsearch-backed).

**What it does:** Full-text search for projects and freelancers with filtering by budget, skills, status, etc.

---

### `apps/search/services/services_autocomplete.py`

**What it is:** Autocomplete services (prefix-based suggestions from `SearchSuggestion`).

---

### `apps/search/services/services_history.py`

**What it is:** Search history services (log queries, get user history).

---

### `apps/search/services/services_saved.py`

**What it is:** Saved search services (create, list, delete saved searches).

---

## frontend

The `frontend/` folder contains the React 18 frontend application built with Vite 6 and Tailwind CSS.

```
frontend/
├── .env.production
├── index.html
├── package.json
├── package-lock.json
├── postcss.config.js
├── tailwind.config.js
├── vite.config.js
├── dist/
│   ├── index.html
│   ├── favicon.ico
│   ├── assets/
│   │   ├── index-BA4w87f2.css
│   │   └── index-BG-265M0.js
│   └── images/
│       ├── home image.png
│       ├── for hiring 1.png
│       ├── for hiring 2.png
│       ├── for hiring 3.png
│       ├── for getting project 1.png
│       ├── for getting project 2.png
│       └── for getting project 3.png
├── public/
│   ├── favicon.ico
│   └── images/
│       └── (same images as dist/)
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── index.css
    ├── api/
    ├── components/
    ├── context/
    ├── hooks/
    ├── pages/
    ├── routes/
    └── utils/
```

---

### `frontend/package.json`

**What it is:** Node.js project configuration for the React frontend.

**Key dependencies:** react 18, react-router-dom 6, axios (HTTP client), @heroicons/react, lucide-react (icons).

**Dev dependencies:** Vite 6, Tailwind CSS 3, PostCSS, Autoprefixer.

**Scripts:** `npm run dev` (start dev server), `npm run build` (production build), `npm run preview` (preview build).

---

### `frontend/index.html`

**What it is:** The single HTML file that Vite serves. Contains `<div id="root">` where React mounts and loads `src/main.jsx` as a module.

---

### `frontend/vite.config.js`

**What it is:** Vite configuration.

**Key settings:** React plugin enabled, path alias `@` → `src/` (so you can import from `@/components/...` instead of `../../../components/...`).

---

### `frontend/tailwind.config.js`

**What it is:** Tailwind CSS configuration.

**What it does:** Tells Tailwind to scan `src/**/*.{js,jsx}` for class names and generate the appropriate CSS.

---

### `frontend/postcss.config.js`

**What it is:** PostCSS configuration with Tailwind and Autoprefixer plugins.

---

### `frontend/src/main.jsx`

**What it is:** React entry point.

**What it does:** Renders `<App />` inside `<BrowserRouter>` (for routing) and `<AuthProvider>` (for authentication state).

---

### `frontend/src/App.jsx`

**What it is:** Main App component with route definitions.

**Routes defined:** `/`, `/login`, `/register`, `/freelancer/worklogs`, `/client/review`.

---

### `frontend/src/index.css`

**What it is:** Global CSS with Tailwind directives (`@tailwind base/components/utilities`) and custom utility classes.

---

### `frontend/src/context/AuthContext.jsx`

**What it is:** React context for authentication state.

**What it provides:** `user`, `login`, `logout`, `register` functions. Manages JWT tokens (access/refresh) in localStorage. Auto-refreshes tokens on expiry.

---

### `frontend/src/context/NotificationContext.jsx`

**What it is:** React context for notification state.

**What it provides:** `notifications`, `unreadCount`, `fetchNotifications`, `markAsRead`, `markAllRead`. WebSocket integration for real-time notifications.

---

### `frontend/src/routes/AppRouter.jsx`

**What it is:** Main router component.

**What it does:** Wraps all routes in `BrowserRouter` + `AuthProvider` + `NotificationProvider`. Defines public routes (landing, login, register), client routes (nested under `<ClientRoute>`), and freelancer routes (nested under `<FreelancerRoute>`).

---

### `frontend/src/routes/ClientRoute.jsx`

**What it is:** Protected route wrapper for client pages.

**What it does:** Checks auth state — redirects to `/login` if user is not authenticated.

---

### `frontend/src/routes/FreelancerRoute.jsx`

**What it is:** Protected route wrapper for freelancer pages.

**What it does:** Same as ClientRoute — checks auth and redirects if needed.

---

### `frontend/src/api/axiosConfig.js`

**What it is:** Axios instance configuration.

**What it does:** Creates an Axios instance with base URL, interceptors for JWT token injection (adds `Authorization: Bearer <token>` header), and 401 refresh handling (auto-refreshes expired tokens).

---

### `frontend/src/api/index.js`

**What it is:** Barrel export for all API modules.

---

### `frontend/src/api/auth.js`

**What it is:** Auth API functions.

**Key functions:** `login`, `register`, `getProfile`, `changePassword`, `requestPasswordReset`, `resetPassword`, `verifyEmail`.

---

### `frontend/src/api/projects.js`

**What it is:** Projects API functions.

**Key functions:** `getProjects`, `getProject`, `createProject`, `updateProject`, `deleteProject`, `getMyProjects`.

---

### `frontend/src/api/bids.js`

**What it is:** Bids API functions.

**Key functions:** `submitBid`, `acceptBid`, `rejectBid`, `withdrawBid`, `getMyBids`, `getProjectBids`.

---

### `frontend/src/api/payments.js`

**What it is:** Payments API functions.

**Key functions:** `createOrder`, `verifyPayment`, `getPaymentHistory`, `getEscrowStatus`.

---

### `frontend/src/api/worklogs.js`

**What it is:** Worklogs API functions.

**Key functions:** `getWorklogs`, `createWorklog`, `submitWorklog`, `approveWorklog`, `generateReport`, `sendAIChat`.

---

### `frontend/src/api/messages.js`

**What it is:** Messaging API functions.

**Key functions:** `getConversations`, `getMessages`, `sendMessage`.

---

### `frontend/src/api/notifications.js`

**What it is:** Notifications API functions.

**Key functions:** `getNotifications`, `markAsRead`, `markAllRead`, `getUnreadCount`.

---

### `frontend/src/api/search.js`

**What it is:** Search API functions.

**Key functions:** `searchProjects`, `searchFreelancers`, `getAutocomplete`, `getSearchHistory`, `saveSearch`.

---

### `frontend/src/hooks/useAuth.js`

**What it is:** Custom hook wrapping `AuthContext`.

**What it does:** Provides convenient access to auth state (`user`, `login`, `logout`, `register`) without importing `useContext` everywhere.

---

### `frontend/src/hooks/useNotifications.js`

**What it is:** Custom hook wrapping `NotificationContext`.

**What it does:** Provides convenient access to notification state and functions.

---

### `frontend/src/hooks/usePagination.js`

**What it is:** Custom hook for paginated API calls.

**What it manages:** `page` state, `loading`, `hasMore`, `loadMore` function. Handles infinite scroll patterns.

---

### `frontend/src/hooks/useWebSocket.js`

**What it is:** Custom hook for WebSocket connections.

**What it provides:** `connect`, `disconnect`, `send`, `onMessage` functions. Used for real-time chat and notifications.

---

### `frontend/src/utils/axiosInstance.js`

**What it is:** Shared Axios instance with interceptors.

---

### `frontend/src/utils/formatCurrency.js`

**What it is:** Currency formatting utility.

**What it does:** Formats amounts as currency strings (e.g., `$1,234.56`).

---

### `frontend/src/utils/formatDate.js`

**What it is:** Date formatting utility.

**What it does:** Formats dates as relative time (e.g., "2 hours ago") or locale-aware strings.

---

### `frontend/src/pages/LandingPage.jsx`

**What it is:** Marketing landing page.

**What it shows:** Hero section, features overview, call-to-action buttons for signing up as client or freelancer.

---

### `frontend/src/pages/auth/LoginPage.jsx`

**What it is:** Login form.

**What it does:** Email + password form, redirects to role-specific dashboard on success.

---

### `frontend/src/pages/auth/RegisterPage.jsx`

**What it is:** Registration form.

**What it does:** Email, password, role selection (client or freelancer).

---

### `frontend/src/pages/auth/GoogleCallbackPage.jsx`

**What it is:** OAuth callback handler for Google sign-in.

**What it does:** Handles the redirect from Google OAuth, extracts the token, and logs the user in.

---

### `frontend/src/pages/shared/NotFoundPage.jsx`

**What it is:** 404 page — shown when a route doesn't match.

---

### `frontend/src/pages/shared/UnauthorizedPage.jsx`

**What it is:** 403 unauthorized page — shown when a user tries to access a page they don't have permission for.

---

### `frontend/src/pages/client/ClientOverviewPage.jsx`

**What it is:** Client dashboard with overview stats.

**What it shows:** Active projects count, pending bids, payment summary.

---

### `frontend/src/pages/client/ClientProjectsPage.jsx`

**What it is:** Client's project listing with status filters.

---

### `frontend/src/pages/client/ClientProjectDetailPage.jsx`

**What it is:** Project detail page with bid management (accept/reject bids).

---

### `frontend/src/pages/client/ClientMessagesPage.jsx`

**What it is:** Client messaging interface.

**What it shows:** Conversation list on the left, chat window on the right.

---

### `frontend/src/pages/client/ClientPaymentsPage.jsx`

**What it is:** Payment history and escrow status for client.

---

### `frontend/src/pages/client/ClientContractDetailPage.jsx`

**What it is:** Contract detail page with milestones and deliverables review.

---

### `frontend/src/pages/client/ClientDeliverableReviewPage.jsx`

**What it is:** Deliverable review page.

**What it does:** Shows deliverable details, allows client to approve or reject with feedback.

---

### `frontend/src/pages/client/ClientReviewPage.jsx`

**What it is:** Review management for client (give/view reviews).

---

### `frontend/src/pages/freelancer/FreelancerOverviewPage.jsx`

**What it is:** Freelancer dashboard with stats.

**What it shows:** Active contracts, earnings summary, pending worklogs.

---

### `frontend/src/pages/freelancer/FreelancerBrowsePage.jsx`

**What it is:** Browse open projects page.

**What it does:** Search and filter projects by budget, skills, category.

---

### `frontend/src/pages/freelancer/FreelancerBidsPage.jsx`

**What it is:** Freelancer's bid listing with status indicators.

---

### `frontend/src/pages/freelancer/FreelancerContractsPage.jsx`

**What it is:** Active contract listing for freelancer.

---

### `frontend/src/pages/freelancer/FreelancerContractDetailPage.jsx`

**What it is:** Contract detail with worklogs, payments, messages.

---

### `frontend/src/pages/freelancer/FreelancerWorklogsPage.jsx`

**What it is:** Worklog management page.

**What it does:** Create, submit worklogs, use AI chat for summaries, view weekly reports.

---

### `frontend/src/pages/freelancer/FreelancerEarningsPage.jsx`

**What it is:** Earnings dashboard with payment history.

---

### `frontend/src/pages/freelancer/FreelancerMessagesPage.jsx`

**What it is:** Freelancer messaging interface.

---

### `frontend/src/pages/freelancer/FreelancerWorkPage.jsx`

**What it is:** Active work page.

**What it does:** AI chat for work summary generation, deliverable creation, worklog submission.

---

### `frontend/src/components/common/Navbar.jsx`

**What it is:** Navigation bar.

**What it shows:** Logo, navigation links, notification bell, user menu with logout.

---

### `frontend/src/components/common/Sidebar.jsx`

**What it is:** Side navigation for dashboard layouts.

**What it does:** Shows different menu items based on user role (client vs freelancer).

---

### `frontend/src/components/common/LoadingSpinner.jsx`

**What it is:** Reusable loading spinner component.

---

### `frontend/src/components/common/ErrorMessage.jsx`

**What it is:** Error display component with optional retry button.

---

### `frontend/src/components/common/ConfirmModal.jsx`

**What it is:** Confirmation dialog modal (e.g., "Are you sure you want to delete?").

---

### `frontend/src/components/common/NotificationBell.jsx`

**What it is:** Notification bell icon with unread count badge and dropdown.

---

### `frontend/src/components/projects/ProjectCard.jsx`

**What it is:** Project summary card.

**What it shows:** Title, budget, skills tags, status badge.

---

### `frontend/src/components/projects/ProjectForm.jsx`

**What it is:** Project create/edit form.

---

### `frontend/src/components/projects/ProjectStatusBadge.jsx`

**What it is:** Colored status badge for project states (OPEN = green, IN_PROGRESS = blue, etc.).

---

### `frontend/src/components/bids/BidCard.jsx`

**What it is:** Bid summary card.

**What it shows:** Freelancer name, amount, status, cover letter preview.

---

### `frontend/src/components/bids/BidForm.jsx`

**What it is:** Bid submission form (amount, cover letter).

---

### `frontend/src/components/payments/EscrowStatus.jsx`

**What it is:** Escrow status indicator component.

---

### `frontend/src/components/payments/PaymentHistory.jsx`

**What it is:** Payment history list component.

---

### `frontend/src/components/worklogs/WorkLogCard.jsx`

**What it is:** Worklog summary card.

**What it shows:** Date, hours worked, status, description preview.

---

### `frontend/src/components/worklogs/WorkLogForm.jsx`

**What it is:** Worklog create/edit form.

---

### `frontend/src/components/worklogs/WeeklyReportCard.jsx`

**What it is:** Weekly report display card with PDF download link.

---

### `frontend/src/components/worklogs/DeliverableCard.jsx`

**What it is:** Deliverable summary card with status and review indicators.

---

### `frontend/src/components/worklogs/DeliveryProofBanner.jsx`

**What it is:** Delivery proof banner with PDF link and report ID.

---

### `frontend/src/components/worklogs/AIChatBox.jsx`

**What it is:** AI chat interface for work summary generation.

**What it does:** Input → AI response → editable report. Freelancer describes their work, AI generates a structured summary.

---

### `frontend/src/components/chat/ChatWindow.jsx`

**What it is:** Chat window with message list.

**What it does:** Shows messages, auto-scrolls to bottom, displays read receipts.

---

### `frontend/src/components/chat/ChatInput.jsx`

**What it is:** Chat message input with send button.

---

### `frontend/src/components/chat/MessageBubble.jsx`

**What it is:** Individual message bubble.

**What it shows:** Sender info, message content, timestamp, read status (double ticks).

---

## deployment

The `deployment/` folder contains deployment scripts and CI/CD configurations.

```
deployment/
├── cicd/
│   ├── README.md
│   ├── .gitkeep
│   ├── aws-codepipeline/
│   │   └── .gitkeep
│   ├── github-actions/
│   │   └── .gitkeep
│   └── scripts/
│       └── .gitkeep
└── scripts/
    ├── backup_db.sh
    └── deploy.sh
```

---

### `deployment/scripts/deploy.sh`

**What it is:** Deployment script.

**What it does:** Pulls latest code, builds Docker images, runs migrations, collects static files, restarts services.

---

### `deployment/scripts/backup_db.sh`

**What it is:** Database backup script.

**What it does:** Runs `pg_dump` with a timestamp to create database backups.

---

### `deployment/cicd/README.md`

**What it is:** CI/CD pipeline documentation.

---

### `deployment/cicd/` (subfolders)

**What it is:** Placeholder directories for future CI/CD setup (AWS CodePipeline, GitHub Actions, custom scripts).

---

## requirements

The `requirements/` folder contains Python dependency files split by environment.

```
requirements/
├── base.txt
├── local.txt
└── production.txt
```

---

### `requirements/base.txt`

**What it is:** Base Python dependencies shared across all environments.

**Key packages:** Django, DRF, Celery, Channels, django-environ, djangorestframework-simplejwt, razorpay, boto3 (AWS S3), elasticsearch-dsl, pyotp (2FA), weasyprint (PDF), groq (AI), langsmith (tracing), etc.

---

### `requirements/local.txt`

**What it is:** Local development dependencies.

**Key packages:** Includes base.txt + django-debug-toolbar, pytest, pytest-django, factory-boy, etc.

---

### `requirements/production.txt`

**What it is:** Production dependencies.

**Key packages:** Includes base.txt + gunicorn, sentry-sdk, etc.

---

## scripts

The `scripts/` folder contains helper shell scripts.

```
scripts/
├── commit_refactor.sh
└── elasticsearch_setup.sh
```

---

### `scripts/commit_refactor.sh`

**What it is:** Git commit helper script for refactoring commits.

**What it does:** Automates the process of staging and committing refactoring changes with a standardized message.

---

### `scripts/elasticsearch_setup.sh`

**What it is:** Elasticsearch index setup script.

**What it does:** Creates and configures Elasticsearch indices for projects and freelancers.

---

## docs

The `docs/` folder contains project documentation.

```
docs/
├── API.md
├── HLD.md
└── folderstructure.md (this file)
```

---

### `docs/API.md`

**What it is:** API documentation.

**What it contains:** Endpoint descriptions, request/response formats, authentication requirements.

---

### `docs/HLD.md`

**What it is:** High-Level Design document.

**What it contains:** System architecture, component diagrams, data flow, technology decisions.

---

## logs

The `logs/` folder contains application log files.

```
logs/
└── freelanceflow.log
```

---

### `logs/freelanceflow.log`

**What it is:** Application log file.

**Key details:** Rotating file handler — max 10MB per file, keeps 5 backup files. Contains request logs, error traces, and application events.

---

## Summary

This project follows a clean, scalable architecture:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + Vite 6 + Tailwind CSS | User interface |
| **API** | Django REST Framework | REST API |
| **WebSocket** | Django Channels + Daphne | Real-time chat |
| **Background Tasks** | Celery + Redis | Async processing (emails, PDFs, AI) |
| **Database** | PostgreSQL (Supabase) / SQLite (local) | Data storage |
| **Search** | Elasticsearch | Full-text search |
| **Cache** | Redis | Performance optimization |
| **Payments** | Razorpay | Escrow payments |
| **AI** | Groq LLM | Work summaries |
| **PDF** | WeasyPrint | Document generation |
| **Deployment** | Docker + Gunicorn | Production hosting |

**Each Django app follows the same pattern:**
```
app/
├── models/          # Database tables
├── serializers/     # Data validation
├── services/        # Business logic (THE important part)
├── views/           # API endpoints
├── urls/            # URL routing
├── selectors.py     # Database queries
├── permissions.py   # Access control
├── signals.py       # Event handlers
├── tasks.py         # Background jobs
├── tests/           # Automated tests
└── logger.py        # Logging helpers
```

This pattern (sometimes called "Service Layer Architecture") keeps business logic in `services/` separate from API concerns in `views/`, making the codebase maintainable as it grows.
