# ============================================================
#  FreelanceFlow — Developer Commands
#  Usage: make <target>
# ============================================================

VENV     = venv
PYTHON   = $(VENV)/bin/python
MANAGE   = $(PYTHON) manage.py
FRONTEND = frontend

.PHONY: help backend frontend-dev worker beat shell migrate makemigrations \
        createsuperuser check clean

help:                          ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Backend ──────────────────────────────────────────────────────────────────

backend:                       ## Run Django dev server on :8000
	$(MANAGE) runserver 8000

test:                          ## Run all tests (--keepdb avoids teardown errors)
	$(MANAGE) test --verbosity=2 --keepdb

test-auth:                     ## Run auth (users app) tests only
	$(MANAGE) test apps.users --verbosity=2 --keepdb

worker:                        ## Run Celery worker (using solo pool for Windows compatibility)
	celery -A config worker -Q freelanceflow,freelanceflow_high_priority,freelanceflow_low_priority --loglevel=info --pool=solo
beat:                         ## Run Celery beat scheduler
	celery -A config beat --loglevel=info

shell:                         ## Open Django shell
	$(MANAGE) shell

migrate:                       ## Apply database migrations
	$(MANAGE) migrate

makemigrations:                ## Create new migrations
	$(MANAGE) makemigrations

createsuperuser:               ## Create a Django superuser
	$(MANAGE) createsuperuser

check:                         ## Run Django system checks
	$(MANAGE) check

# ── Frontend ─────────────────────────────────────────────────────────────────

frontend-dev:                  ## Run Vite dev server on :3000
	cd $(FRONTEND) && npm run dev

frontend-build:                ## Build frontend for production
	cd $(FRONTEND) && npm run build

# ── Utility ──────────────────────────────────────────────────────────────────

clean:                         ## Remove .pyc files and __pycache__
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
