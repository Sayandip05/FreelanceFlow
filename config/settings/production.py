from .base import *

DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# CORS - configured via environment variable
# CORS_ALLOWED_ORIGINS is set in base.py from env variable
# Example in .env: CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Storage in production - WhiteNoise for static, Azure Blob Storage for media
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
DEFAULT_FILE_STORAGE = "storages.backends.azure_storage.AzureStorage"
AZURE_CONNECTION_STRING = AZURE_STORAGE_CONNECTION_STRING
AZURE_CONTAINER = AZURE_CONTAINER_NAME

# Logging — override base.py to use JSON formatter in production
# The file handler (logs/freelanceflow.log) and all loggers are
# inherited from base.py; we define the json formatter and swap it here.
LOGGING["formatters"]["json"] = {
    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
}
LOGGING["handlers"]["console"]["formatter"] = "json"
LOGGING["handlers"]["file"]["formatter"] = "json"

# Sentry
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment="production",
    )

# Admin email for errors
ADMINS = [("Admin", "admin@freelanceflow.com")]

# Celery production settings
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Cache - use Redis for session and cache
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
        },
        "KEY_PREFIX": "freelanceflow",
        "TIMEOUT": 300,
    }
}

# Database connection pool
if env("DATABASE_URL", default=""):
    DATABASES = {
        "default": env.db_url("DATABASE_URL")
    }
    DATABASES["default"]["CONN_MAX_AGE"] = 60
    DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
    DATABASES["default"]["OPTIONS"] = {
        "connect_timeout": 10,
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DATABASE_NAME", default="freelanceflow"),
            "USER": env("DATABASE_USER", default="postgres"),
            "PASSWORD": env("DATABASE_PASSWORD", default="postgres"),
            "HOST": env("DATABASE_HOST", default="localhost"),
            "PORT": env("DATABASE_PORT", default="5432"),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                "connect_timeout": 10,
            },
        }
    }
