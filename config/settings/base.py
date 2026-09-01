import os
import logging
from pathlib import Path

import environ

# Suppress django-environ warnings about invalid lines in .env file
logging.getLogger("environ").setLevel(logging.ERROR)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    DJANGO_ENV=(str, "local"),
    SECRET_KEY=(str, "change-me-in-production"),
    ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(str, "sqlite:///db.sqlite3"),
    DATABASE_NAME=(str, "freelanceflow"),
    DATABASE_USER=(str, "postgres"),
    DATABASE_PASSWORD=(str, "postgres"),
    DATABASE_HOST=(str, "localhost"),
    DATABASE_PORT=(str, "5432"),
    REDIS_URL=(str, "redis://localhost:6379/0"),
    CELERY_BROKER_URL=(str, "redis://localhost:6379/0"),
    CELERY_RESULT_BACKEND=(str, "redis://localhost:6379/0"),
    RAZORPAY_KEY_ID=(str, ""),
    RAZORPAY_KEY_SECRET=(str, ""),
    RAZORPAY_WEBHOOK_SECRET=(str, ""),
    RAZORPAY_ACCOUNT_NUMBER=(str, ""),
    AZURE_STORAGE_CONNECTION_STRING=(str, ""),
    AZURE_CONTAINER_NAME=(str, "media"),
    QDRANT_URL=(str, ""),
    QDRANT_API_KEY=(str, ""),
    GROQ_API_KEY=(str, ""),
    GROQ_MODEL=(str, "openai/gpt-oss-120b"),
    GEMINI_API_KEY=(str, ""),
    GEMINI_EMBEDDING_MODEL=(str, "gemini-embedding-001"),
    LANGSMITH_API_KEY=(str, ""),
    LANGSMITH_PROJECT=(str, "freelanceflow"),
    LANGSMITH_TRACING=(bool, False),
    LANGCHAIN_API_KEY=(str, ""),
    LANGCHAIN_PROJECT=(str, ""),
    LANGCHAIN_TRACING_V2=(str, "false"),
    LANGCHAIN_ENDPOINT=(str, ""),
    ELASTICSEARCH_URL=(str, "http://localhost:9200"),
    EMAIL_HOST=(str, "localhost"),
    EMAIL_PORT=(int, 587),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    DEFAULT_FROM_EMAIL=(str, "noreply@freelanceflow.com"),
    FRONTEND_URL=(str, "http://localhost:3000"),
    BACKEND_URL=(str, "http://localhost:8000"),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000", "http://127.0.0.1:3000"]),
    PLATFORM_CUT_PERCENTAGE=(int, 10),
    # Google OAuth
    GOOGLE_CLIENT_ID=(str, ""),
    GOOGLE_CLIENT_SECRET=(str, ""),
)

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
DJANGO_ENV = env("DJANGO_ENV")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

DJANGO_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "channels",
    "django_celery_beat",
    "django_elasticsearch_dsl",
    "django_extensions",
    "axes",
]

LOCAL_APPS = [
    "core",
    "apps.users",
    "apps.projects",
    "apps.bidding",
    "apps.payments",
    "apps.worklogs",
    "apps.messaging",
    "apps.notifications",
    "apps.search",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "core.middleware_shutdown.GracefulShutdownMiddleware",  # Graceful shutdown - must be first
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "core.middleware.SecurityHeadersMiddleware",
    "core.middleware.CacheControlMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.RequestLoggingMiddleware",  # After auth so request.user is set
    "core.middleware.PerformanceProfilingMiddleware",  # SQL profiling, N+1 detection, and slow query monitoring
    "axes.middleware.AxesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.CORSCustomMiddleware",
]


ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db_url("DATABASE_URL", default="sqlite:///db.sqlite3")
}
# Enable Persistent Database Connections (Built-in Connection Pooling)
# Keep database connections open for up to 10 minutes (600 seconds) to avoid TCP overhead
DATABASES["default"]["CONN_MAX_AGE"] = 600
# Verify connection health before recycling it (guards against dropped/stale DB sockets)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultsPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
}

from corsheaders.defaults import default_headers

# CORS
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    "ngrok-skip-browser-warning",
]

# Redis
REDIS_URL = env("REDIS_URL")

# Channels Configuration (WebSocket with Upstash Redis)
# expiry=60  → messages older than 60 seconds are dropped (stale real-time events are useless)
# capacity=100 → max 100 messages buffered per channel before back-pressure kicks in
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
        "CONFIG": {
            "expiry": 60,     # seconds — bid updates / milestone drafts / worklog events
            "capacity": 100,  # messages per channel group
        },
    }
}

# Celery Configuration (Upstash Redis)
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_RESULT_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Celery Queue Configuration (Isolation)
CELERY_TASK_DEFAULT_QUEUE = "freelanceflow"
CELERY_TASK_DEFAULT_EXCHANGE = "freelanceflow"
CELERY_TASK_DEFAULT_ROUTING_KEY = "freelanceflow"

# Celery Result Backend & Broker Settings (Upstash Redis)
CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {
    "retry_on_timeout": True,
    "health_check_interval": 30,
}
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "retry_on_timeout": True,
    "health_check_interval": 30,
}

# Celery Broker Settings (Upstash Redis)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
import ssl
import certifi

if CELERY_BROKER_URL.startswith("rediss://"):
    CELERY_BROKER_USE_SSL = {
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
        "ssl_ca_certs": certifi.where(),
    }
else:
    CELERY_BROKER_USE_SSL = None

if CELERY_RESULT_BACKEND.startswith("rediss://"):
    CELERY_REDIS_BACKEND_USE_SSL = {
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
        "ssl_ca_certs": certifi.where(),
    }
else:
    CELERY_REDIS_BACKEND_USE_SSL = None



# Task execution settings
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# ── TTL / Expiry Settings ────────────────────────────────────────────────────
# Task result expiry: how long Celery keeps the result in Redis after completion.
# After 1 hour nobody is waiting for the result anymore (user has moved on).
CELERY_RESULT_EXPIRES = 3600  # 1 hour in seconds

# Task queue expiry: how long a queued task waits before being dropped.
# Default for LOW-priority tasks (PDF, reports). Payment tasks override this
# individually with expires=None so money tasks are never silently dropped.
CELERY_TASK_EXPIRES = 7200  # 2 hours — applies to all tasks unless overridden

# Beat schedule (for periodic tasks)
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Celery Beat — Periodic Task Schedule
# Defines the recurring tasks run by `celery beat`.
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    # ── Progress Reports ──────────────────────────────────────────────────────
    # Fires at 12:05 AM every day.
    # Checks all ReportSchedules where next_report_date <= today and enqueues
    # AI report generation for each. Advances next_report_date after queuing.
    "trigger-scheduled-reports-daily": {
        "task": "apps.worklogs.tasks.trigger_scheduled_reports",
        "schedule": crontab(hour=0, minute=5),
    },
    # Fires at 9:00 AM every day.
    # Sends freelancer in-app notification if report is due within 3 days.
    "check-upcoming-report-deadlines-daily": {
        "task": "apps.worklogs.tasks.check_upcoming_report_deadlines",
        "schedule": crontab(hour=9, minute=0),
    },
    # ── Legacy Weekly Sweep (contracts without a ReportSchedule) ─────────────
    # Runs every Sunday at 11:59 PM.
    # Targets contracts that don't have a configured ReportSchedule.
    # Contracts with an active ReportSchedule are handled by the daily task above.
    "generate-weekly-reports-sunday": {
        "task": "apps.worklogs.tasks.generate_weekly_reports_for_all_contracts",
        "schedule": crontab(hour=23, minute=59, day_of_week=0),
    },
}

# Razorpay
RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = env("RAZORPAY_WEBHOOK_SECRET")
RAZORPAY_ACCOUNT_NUMBER = env("RAZORPAY_ACCOUNT_NUMBER")

# Azure Blob Storage
# Used for all media & PDF uploads: progress reports, delivery proofs, avatars, attachments.
# Container: AZURE_CONTAINER_NAME (default: "media")
# Access: Private container, 7-day SAS URLs generated on upload.
AZURE_STORAGE_CONNECTION_STRING = env("AZURE_STORAGE_CONNECTION_STRING", default="")
AZURE_CONTAINER_NAME = env("AZURE_CONTAINER_NAME", default="media")

# Groq (Primary LLM for AI chat and reports)
GROQ_API_KEY = env("GROQ_API_KEY")
GROQ_MODEL = env("GROQ_MODEL")

# Google Gemini (Fallback LLM & Vector Embeddings for Qdrant)
GEMINI_API_KEY = env("GEMINI_API_KEY")
GEMINI_EMBEDDING_MODEL = env("GEMINI_EMBEDDING_MODEL", default="gemini-embedding-001")

# Qdrant Vector Cloud (for contract scope and requirement grounding)
QDRANT_URL = env("QDRANT_URL")
QDRANT_API_KEY = env("QDRANT_API_KEY")

# LangSmith (for AI tracing and monitoring)
# Fallback to LANGCHAIN_* keys if they are present in .env
LANGSMITH_API_KEY = env("LANGSMITH_API_KEY", default=env("LANGCHAIN_API_KEY", default=""))
LANGSMITH_PROJECT = env("LANGSMITH_PROJECT", default=env("LANGCHAIN_PROJECT", default="freelanceflow"))
LANGSMITH_TRACING = env("LANGSMITH_TRACING", default=env("LANGCHAIN_TRACING_V2", default="false"))
LANGSMITH_ENDPOINT = env("LANGSMITH_ENDPOINT", default=env("LANGCHAIN_ENDPOINT", default="https://api.smith.langchain.com"))

# Set LangSmith environment variables for tracing
is_tracing_enabled = str(LANGSMITH_TRACING).lower() in ["true", "1", "yes"]

if is_tracing_enabled and LANGSMITH_API_KEY:
    import os

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT

# Elasticsearch
ELASTICSEARCH_URL = env("ELASTICSEARCH_URL")
ELASTICSEARCH_DSL = {
    "default": {
        "hosts": ELASTICSEARCH_URL,
        "timeout": 20,
    },
}

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# Frontend / Backend URL (for email links & OAuth redirects)
FRONTEND_URL = env("FRONTEND_URL")
BACKEND_URL = env("BACKEND_URL")

# Google OAuth2
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET")

# Platform Settings
PLATFORM_CUT_PERCENTAGE = env("PLATFORM_CUT_PERCENTAGE")

# Cache Configuration (Redis / Upstash)
# HiredisParser was removed in redis-py 5.x — do not set PARSER_CLASS.
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
                "ssl_cert_reqs": None,
            },
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "IGNORE_EXCEPTIONS": True,  # Degrade gracefully when Redis is down
        },
        "KEY_PREFIX": "freelanceflow",
        "TIMEOUT": 300,  # 5 minutes default
        "VERSION": 1,
    },
    # Fallback in-process cache used by Django Axes when Redis is unavailable.
    "axes": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "axes",
    },
}

# Django Axes (Brute Force Protection)
# Using the DB handler so login protection works without a running Redis instance.
AXES_ENABLED = True
AXES_HANDLER = "axes.handlers.database.AxesDatabaseHandler"
AXES_LOGIN_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 300
AXES_LOCK_OUT = True

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Session Settings
# Use DB-backed sessions so login works without a local Redis instance.
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_NAME = "ff_sessionid"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
SESSION_COOKIE_SAMESITE = "Lax"

# CSRF Settings
CSRF_COOKIE_NAME = "ff_csrftoken"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_USE_SESSIONS = False

# =============================================================================
# LOGGING — Centralized config (all environments)
# =============================================================================
# All app logs go to ONE rotating file: logs/freelanceflow.log
# Each app has its own named logger (apps.bidding, apps.payments, etc.)
# Production overrides the handler to use JSON format.
# =============================================================================

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        # Plain text — used in local dev
        "standard": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },

    "handlers": {
        # Console — always on
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        # Single rotating file — ALL app logs go here
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "freelanceflow.log",
            "maxBytes": 10 * 1024 * 1024,   # 10 MB
            "backupCount": 5,
            "formatter": "standard",
            "encoding": "utf-8",
        },
    },

    # Root logger — catches anything not matched below
    "root": {
        "handlers": ["console", "file"],
        "level": "WARNING",
    },

    "loggers": {
        # ── FreelanceFlow apps ─────────────────────────────────────────────
        "apps.users": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.projects": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.bidding": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.payments": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.worklogs": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.messaging": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.notifications": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.search": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        # ── Django internals ───────────────────────────────────────────────
        "django": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": False,
        },
        # ── Third-party noise suppression ──────────────────────────────────
        "celery": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "environ": {
            "handlers": [],
            "level": "CRITICAL",
            "propagate": False,
        },
    },
}

