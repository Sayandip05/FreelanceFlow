import os
import signal
import logging
from celery import Celery
from celery.signals import worker_shutdown, worker_shutting_down
from kombu import Queue

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("freelanceflow")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Graceful shutdown configuration
app.conf.update(
    # ============================================
    # QUEUE CONFIGURATION (Upstash Redis Isolation)
    # ============================================
    # Default queue name for isolation from other projects
    task_default_queue='freelanceflow',
    task_default_exchange='freelanceflow',
    task_default_routing_key='freelanceflow',
    
    # Define queues explicitly
    task_queues=(
        Queue('freelanceflow', routing_key='freelanceflow'),
        Queue('freelanceflow_high_priority', routing_key='freelanceflow.high'),
        Queue('freelanceflow_low_priority', routing_key='freelanceflow.low'),
    ),
    
    # Route specific tasks to different priority queues
    task_routes={
        # High priority tasks (payments, webhooks)
        'apps.payments.tasks.process_razorpay_webhook_task': {
            'queue': 'freelanceflow_high_priority',
            'routing_key': 'freelanceflow.high',
        },
        'apps.payments.tasks.razorpay_transfer_to_freelancer_task': {
            'queue': 'freelanceflow_high_priority',
            'routing_key': 'freelanceflow.high',
        },
        'apps.payments.tasks.process_razorpay_refund_task': {
            'queue': 'freelanceflow_high_priority',
            'routing_key': 'freelanceflow.high',
        },
        
        # Low priority tasks (reports, PDFs)
        'apps.worklogs.tasks.generate_pdf_task': {
            'queue': 'freelanceflow_low_priority',
            'routing_key': 'freelanceflow.low',
        },
        'apps.worklogs.tasks.generate_ai_report_task': {
            'queue': 'freelanceflow_low_priority',
            'routing_key': 'freelanceflow.low',
        },
        'apps.worklogs.tasks.generate_weekly_reports_for_all_contracts': {
            'queue': 'freelanceflow_low_priority',
            'routing_key': 'freelanceflow.low',
        },
        'apps.worklogs.tasks.trigger_scheduled_reports': {
            'queue': 'freelanceflow_low_priority',
            'routing_key': 'freelanceflow.low',
        },
        'apps.worklogs.tasks.check_upcoming_report_deadlines': {
            'queue': 'freelanceflow_low_priority',
            'routing_key': 'freelanceflow.low',
        },
        'apps.worklogs.tasks.notify_client_new_report': {
            'queue': 'freelanceflow_low_priority',
            'routing_key': 'freelanceflow.low',
        },
        'apps.worklogs.tasks.notify_freelancer_report_upcoming': {
            'queue': 'freelanceflow_low_priority',
            'routing_key': 'freelanceflow.low',
        },
        
        # Default queue for all other tasks
        '*': {
            'queue': 'freelanceflow',
            'routing_key': 'freelanceflow',
        },
    },
    
    # ============================================
    # WORKER CONFIGURATION
    # ============================================
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
    
    # ============================================
    # REDIS CONNECTION CONFIGURATION (Upstash)
    # ============================================
    # Connection pool settings for Upstash Redis
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Redis connection pool settings
    broker_pool_limit=10,
    
    # Result backend settings
    result_backend_transport_options={
        'master_name': 'mymaster',
        'socket_keepalive': True,
        'socket_keepalive_options': {
            1: 1,  # TCP_KEEPIDLE
            2: 1,  # TCP_KEEPINTVL
            3: 5,  # TCP_KEEPCNT
        },
        'retry_on_timeout': True,
        'health_check_interval': 30,
    },
    
    # Broker transport options for Upstash Redis
    broker_transport_options={
        'visibility_timeout': 3600,  # 1 hour
        'fanout_prefix': True,
        'fanout_patterns': True,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            1: 1,  # TCP_KEEPIDLE
            2: 1,  # TCP_KEEPINTVL
            3: 5,  # TCP_KEEPCNT
        },
        'retry_on_timeout': True,
        'health_check_interval': 30,
    },
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
