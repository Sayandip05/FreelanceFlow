from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, FreelancerProfile, ClientProfile
from .tasks import send_welcome_email_task


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create appropriate profile when a new user is created.
    """
    if created:
        if instance.role == User.Roles.FREELANCER:
            FreelancerProfile.objects.create(user=instance)
        elif instance.role == User.Roles.CLIENT:
            ClientProfile.objects.create(user=instance)
        
        # Send welcome email after transaction commits
        transaction.on_commit(
            lambda: send_welcome_email_task.delay(instance.id)
        )


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
