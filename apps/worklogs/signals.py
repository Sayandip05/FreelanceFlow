"""
Signals for worklogs app.
Triggers asynchronous Qdrant vectorization when a Contract becomes ACTIVE.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.bidding.models import Contract

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Contract)
def on_contract_status_changed(sender, instance, created, **kwargs):
    """
    When a contract is created or updated to ACTIVE status, trigger async Qdrant collection initialization.
    """
    is_active = getattr(instance, "is_active", False) or getattr(instance, "status", "") == "ACTIVE"
    if is_active:
        try:
            from apps.worklogs.tasks import initialize_qdrant_collection_task
            initialize_qdrant_collection_task.delay(instance.id)
            logger.info("Enqueued Qdrant vectorization for Contract #%s", instance.id)
        except Exception as e:
            logger.warning("Could not enqueue Qdrant task for Contract #%s: %s", instance.id, e)
