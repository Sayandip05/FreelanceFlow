"""
Digest Email Services
"""
from django.db import transaction
from .models_extended import DigestEmail


@transaction.atomic
def create_digest_subscription(user, frequency='WEEKLY'):
    """Create digest email subscription"""
    return DigestEmail.objects.create(
        user=user,
        frequency=frequency,
        is_enabled=True
    )


def get_pending_digests():
    """Get digests that need to be sent"""
    from django.utils import timezone
    
    return DigestEmail.objects.filter(
        is_enabled=True,
        next_send_at__lte=timezone.now()
    )


@transaction.atomic
def send_digest(digest_id):
    """Send digest email"""
    from datetime import timedelta
    
    digest = DigestEmail.objects.get(id=digest_id)
    
    # Send email logic here
    
    # Update timestamps
    digest.last_sent_at = timezone.now()
    if digest.frequency == 'DAILY':
        digest.next_send_at = timezone.now() + timedelta(days=1)
    elif digest.frequency == 'WEEKLY':
        digest.next_send_at = timezone.now() + timedelta(weeks=1)
    digest.save()
