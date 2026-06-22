"""
User Online Status Services
Tracks user online/offline status and last seen
"""
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models_extended import UserOnlineStatus


@transaction.atomic
def update_online_status(user, is_online=True, status_message=None):
    """
    Update user's online status
    
    Args:
        user: User instance
        is_online: Boolean indicating online status
        status_message: Optional status message
    
    Returns:
        UserOnlineStatus instance
    """
    status, created = UserOnlineStatus.objects.update_or_create(
        user=user,
        defaults={
            'is_online': is_online,
            'last_seen': timezone.now(),
            'status_message': status_message
        }
    )
    return status


def set_user_online(user, status_message=None):
    """Mark user as online"""
    return update_online_status(user, is_online=True, status_message=status_message)


def set_user_offline(user):
    """Mark user as offline"""
    return update_online_status(user, is_online=False)


def update_last_seen(user):
    """Update user's last seen timestamp"""
    UserOnlineStatus.objects.update_or_create(
        user=user,
        defaults={'last_seen': timezone.now()}
    )


def get_user_status(user):
    """
    Get user's online status
    
    Returns:
        Dict with is_online, last_seen, status_message
    """
    try:
        status = UserOnlineStatus.objects.get(user=user)
        return {
            'is_online': status.is_online,
            'last_seen': status.last_seen,
            'status_message': status.status_message
        }
    except UserOnlineStatus.DoesNotExist:
        return {
            'is_online': False,
            'last_seen': None,
            'status_message': None
        }


def is_user_online(user):
    """Check if user is currently online"""
    try:
        status = UserOnlineStatus.objects.get(user=user)
        
        # Consider user offline if last seen > 5 minutes ago
        if status.is_online:
            time_threshold = timezone.now() - timedelta(minutes=5)
            if status.last_seen < time_threshold:
                # Auto-mark as offline
                status.is_online = False
                status.save()
                return False
        
        return status.is_online
    except UserOnlineStatus.DoesNotExist:
        return False


def get_online_users(limit=100):
    """
    Get list of currently online users
    
    Returns:
        QuerySet of User objects
    """
    from .models import User
    
    # Users online in last 5 minutes
    time_threshold = timezone.now() - timedelta(minutes=5)
    
    online_user_ids = UserOnlineStatus.objects.filter(
        is_online=True,
        last_seen__gte=time_threshold
    ).values_list('user_id', flat=True)
    
    return User.objects.filter(id__in=online_user_ids)[:limit]


def get_online_count():
    """Get count of currently online users"""
    time_threshold = timezone.now() - timedelta(minutes=5)
    
    return UserOnlineStatus.objects.filter(
        is_online=True,
        last_seen__gte=time_threshold
    ).count()


def set_status_message(user, message):
    """Set user's status message"""
    UserOnlineStatus.objects.update_or_create(
        user=user,
        defaults={'status_message': message}
    )


def clear_status_message(user):
    """Clear user's status message"""
    UserOnlineStatus.objects.update_or_create(
        user=user,
        defaults={'status_message': None}
    )


def cleanup_stale_online_status():
    """
    Cleanup task to mark users as offline if inactive > 10 minutes
    Should be run periodically (e.g., every 5 minutes via Celery)
    """
    time_threshold = timezone.now() - timedelta(minutes=10)
    
    updated = UserOnlineStatus.objects.filter(
        is_online=True,
        last_seen__lt=time_threshold
    ).update(is_online=False)
    
    return updated
