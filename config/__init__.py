"""
FreelanceFlow Configuration Package.
Registers graceful shutdown handlers on Django startup.
"""
from .celery import app as celery_app

__all__ = ("celery_app",)

# Register graceful shutdown handlers
try:
    from .signals import register_shutdown_handlers
    register_shutdown_handlers()
except ImportError:
    # Signals module not available yet (during initial setup)
    pass
