from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".ngrok.io", ".ngrok-free.app"]

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
ELASTICSEARCH_DSL_AUTOSYNC = False
# Use the no-op base processor so no ES connections are attempted on signals.
ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = "django_elasticsearch_dsl.signals.BaseSignalProcessor"

# Debug toolbar (optional)
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
# INTERNAL_IPS = ["127.0.0.1"]

# Logging — inherited from base.py (console + file handler)
# No override needed for local development.

