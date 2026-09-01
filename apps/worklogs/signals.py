"""
Signals for worklogs app.
Triggers asynchronous Qdrant vectorization when a Contract becomes ACTIVE.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.bidding.models import Contract
from apps.worklogs.models import WorkLog, Deliverable
from apps.payments.models import PaymentMilestone

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


@receiver(post_save, sender=WorkLog)
def on_worklog_saved(sender, instance, created, **kwargs):
    """
    Broadcast work log updates to contract view.
    """
    try:
        from apps.payments.consumers import push_contract_event
        push_contract_event(
            contract_id=instance.contract_id,
            event_type="worklog_update",
            payload={"worklog_id": instance.id}
        )
    except Exception as e:
        logger.warning("Failed to push worklog update event: %s", e)


@receiver(post_save, sender=Deliverable)
def on_deliverable_saved(sender, instance, created, **kwargs):
    """
    Broadcast deliverable updates to contract view.
    """
    try:
        from apps.payments.consumers import push_contract_event
        push_contract_event(
            contract_id=instance.contract_id,
            event_type="worklog_update",
            payload={"deliverable_id": instance.id}
        )
    except Exception as e:
        logger.warning("Failed to push deliverable update event: %s", e)


@receiver(post_save, sender=PaymentMilestone)
def on_payment_milestone_saved(sender, instance, created, **kwargs):
    """
    When a milestone is created or updated, re-sync the Qdrant collection to keep 
    the AI Assistant grounded with the latest milestone scope/status.
    """
    try:
        from apps.worklogs.tasks import initialize_qdrant_collection_task
        initialize_qdrant_collection_task.delay(instance.contract_id)
        logger.info("Enqueued Qdrant vectorization for Contract #%s due to milestone update", instance.contract_id)
    except Exception as e:
        logger.warning("Could not enqueue Qdrant task for Contract #%s: %s", instance.contract_id, e)
