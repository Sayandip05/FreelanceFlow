import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, FreelancerProfile, ClientProfile
from .tasks import send_welcome_email_task
logger = logging.getLogger(__name__)


def _dispatch_welcome_email(user_id: int) -> None:
    """
    Fire the welcome-email Celery task.
    Wrapped in try/except so that a missing Redis/Celery broker during local
    development or seeding does NOT crash the transaction on_commit hook —
    the user row and profile are always committed successfully regardless.
    """
    try:
        send_welcome_email_task.delay(user_id)
    except Exception as exc:
        logger.warning(
            "Could not dispatch welcome email for user_id=%s "
            "(Celery/Redis unavailable): %s",
            user_id, exc,
        )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create appropriate profile when a new user is created and schedule
    the welcome email task after the transaction commits.
    """
    if created:
        if instance.role == User.Roles.FREELANCER:
            FreelancerProfile.objects.create(user=instance)
        elif instance.role == User.Roles.CLIENT:
            ClientProfile.objects.create(user=instance)

        # Dispatch welcome email only after the DB transaction commits.
        # Uses a resilient wrapper so Redis downtime doesn't abort seeding.
        transaction.on_commit(lambda: _dispatch_welcome_email(instance.id))


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save profile when user is saved (ensures profile exists).
    """
    if instance.role == User.Roles.FREELANCER:
        try:
            instance.freelancer_profile.save()
        except FreelancerProfile.DoesNotExist:
            FreelancerProfile.objects.create(user=instance)
    elif instance.role == User.Roles.CLIENT:
        try:
            instance.client_profile.save()
        except ClientProfile.DoesNotExist:
            ClientProfile.objects.create(user=instance)
 
