import os
import signal
import logging
from celery import Celery
from celery.signals import worker_shutdown, worker_shutting_down

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("freelanceflow")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Graceful shutdown configuration
app.conf.update(
    # Worker will restart after processing this many tasks (prevents memory leaks)
    worker_max_tasks_per_child=1000,
    
    # Enable worker pool restarts
    worker_pool_restarts=True,
    
    # Soft time limit (task will receive exception)
    task_soft_time_limit=300,  # 5 minutes
    
    # Hard time limit (task will be killed)
    task_time_limit=600,  # 10 minutes
    
    # Acknowledge tasks after execution (not before)
    task_acks_late=True,
    
    # Don't prefetch tasks (better for long-running tasks)
    worker_prefetch_multiplier=1,
    
    # Reject tasks on worker shutdown
    task_reject_on_worker_lost=True,
    
    # Send task events for monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


@worker_shutting_down.connect
def worker_shutting_down_handler(sig, how, exitcode, **kwargs):
    """
    Called when worker is shutting down.
    Clean up resources before worker exits.
    """
    logger.info(f"Celery worker shutting down (signal: {sig}, exitcode: {exitcode})")
    
    try:
        # Close database connections
        from django.db import connections
        for conn in connections.all():
            conn.close()
        logger.info("Closed all database connections")
        
        # Close cache connections
        from django.core.cache import cache
        if hasattr(cache, 'close'):
            cache.close()
        logger.info("Closed cache connections")
        
    except Exception as e:
        logger.error(f"Error during Celery worker shutdown: {e}", exc_info=True)


@worker_shutdown.connect
def worker_shutdown_handler(sender, **kwargs):
    """
    Called after worker has shut down.
    Final cleanup operations.
    """
    logger.info("Celery worker shutdown complete")


def handle_sigterm(signum, frame):
    """
    Handle SIGTERM signal for graceful shutdown.
    """
    logger.info("Received SIGTERM, initiating graceful Celery worker shutdown...")
    # Celery will handle the actual shutdown
    raise SystemExit(0)


# Register SIGTERM handler
signal.signal(signal.SIGTERM, handle_sigterm)
