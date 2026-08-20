from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver", ".ngrok.io", ".ngrok-free.app"]

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable HTTPS requirements for local development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ── Elasticsearch (local dev) ─────────────────────────────────────────────────
# Disable automatic ES index syncing on model saves so the app runs fully
# without a local Elasticsearch instance. The custom search signals in
# apps/search/signals.py also catch connection errors defensively.
# When ES IS running, rebuild the index manually:
#   python manage.py search_index --rebuild
ELASTICSEARCH_DSL_AUTOSYNC = True
# Use the real-time signal processor to automatically sync models to ES on save.
ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = "django_elasticsearch_dsl.signals.RealTimeSignalProcessor"

# Debug toolbar (optional)
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
# INTERNAL_IPS = ["127.0.0.1"]

# ── Database ──────────────────────────────────────────────────────────────────
# Reads DATABASE_URL from .env (set to your local PostgreSQL or Supabase URL).
# For test runs, use config/settings/test.py instead (via pytest.ini).
# Example .env:
#   DATABASE_URL=postgres://user:password@localhost:5432/freelanceflow

# ── Channels WebSocket Layer (local dev) ──────────────────────────────────────
# Use InMemoryChannelLayer so WebSocket real-time chat connects instantly
# without requiring an active local Redis server.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

# ── Local Cache Configuration ──────────────────────────────────────────────────
# Use LocMemCache instead of Redis for caching in local development to avoid
# extra dependencies and comply with the strict project rules.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "freelanceflow-local",
    },
    "axes": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "axes",
    },
}

# ── Throttle override for local dev & load testing ────────────────────────────
# In production, AuthRateThrottle = 5/minute. Locally we raise all limits so
# Locust virtual users (all sharing 127.0.0.1) are never blocked by rate limits.
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "10000/hour",
    "user": "100000/hour",
    "auth": "1000/minute",   # was 5/minute — allows Locust concurrent logins
}

# Disable django-axes lockout during local development and load testing
AXES_ENABLED = False
