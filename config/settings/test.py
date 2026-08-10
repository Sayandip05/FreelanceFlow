"""
Test settings for FreelanceFlow.

Inherits from local.py (DEBUG=True, console email, etc.) and overrides
database config to use an in-memory SQLite instance for maximum speed and
isolation. No PostgreSQL, Redis, or Celery needed to run the test suite.

Usage (via pytest.ini):
    DJANGO_SETTINGS_MODULE = config.settings.test
"""
from .local import *

# ── Database ──────────────────────────────────────────────────────────────────
# Always use in-memory SQLite for tests — fast, isolated, no external services.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        # Keep the test DB in a predictable place so Django doesn't need to
        # create a separate "test_" prefix database.
        "TEST": {
            "NAME": ":memory:",
        },
    }
}

# ── Cache ─────────────────────────────────────────────────────────────────────
# Use isolated in-memory cache for tests to avoid remote Redis rate-limit pollution.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    },
    "axes": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-axes-cache",
    },
}

# ── Celery / Redis ────────────────────────────────────────────────────────────
# Run tasks synchronously in tests so we never need a running broker.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ── Password hashing ─────────────────────────────────────────────────────────
# Use the fastest hasher in tests — security not required here.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ── Email ─────────────────────────────────────────────────────────────────────
# Capture all emails in-memory; access via django.core.mail.outbox.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ── Elasticsearch ─────────────────────────────────────────────────────────────
# Already disabled in local.py via ELASTICSEARCH_DSL_AUTOSYNC = False.
# Explicit no-op signal processor to prevent any ES connection attempts.
ELASTICSEARCH_DSL_AUTOSYNC = False
ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = "django_elasticsearch_dsl.signals.BaseSignalProcessor"

# ── Throttling ────────────────────────────────────────────────────────────────
# Relax rate limits during test runs so batch test cases don't trip 429.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10000/min",
        "user": "10000/min",
        "auth": "10000/min",
        "oauth": "10000/min",
    },
}

# ── Logging ───────────────────────────────────────────────────────────────────
# Silence all app loggers during tests to keep output clean.
_app_loggers = ["apps.users", "apps.projects", "apps.bidding", "apps.payments",
                "apps.worklogs", "apps.messaging", "apps.notifications", "apps.search"]
for _logger in _app_loggers:
    if _logger in LOGGING["loggers"]:
        LOGGING["loggers"][_logger]["level"] = "CRITICAL"
# Also silence Django request/db loggers
for _logger in ["django", "django.request", "django.db.backends"]:
    if _logger in LOGGING["loggers"]:
        LOGGING["loggers"][_logger]["level"] = "CRITICAL"
