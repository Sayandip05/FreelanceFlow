from django.db.models import QuerySet
from apps.notifications.models import Notification
def get_notification_by_id(notification_id: int) -> Notification | None:
    """Get a notification by ID."""
    try:
        return Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return None


def get_user_notifications(user) -> QuerySet[Notification]:
    """Get all notifications for a user, ordered by newest first."""
    return Notification.objects.filter(recipient=user)


def get_unread_notifications(user) -> QuerySet[Notification]:
    """Get unread notifications for a user."""
    return Notification.objects.filter(recipient=user, is_read=False)


def get_unread_count(user) -> int:
    """Get count of unread notifications for a user."""
    return Notification.objects.filter(recipient=user, is_read=False).count()
