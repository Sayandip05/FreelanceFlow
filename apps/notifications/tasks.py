from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from apps.notifications.selectors import get_notification_by_id


@shared_task(bind=True, max_retries=3)
def send_notification_email(self, notification_id: int):
    """
    Send email notification to user.
    Called asynchronously when in-app notification is created.
    """
    from apps.notifications.models import Notification
    try:
        notification = Notification.objects.select_related('recipient').get(id=notification_id)
        user = notification.recipient
        
        # Only send if user has email notifications enabled
        if hasattr(user, 'profile') and not user.profile.email_notifications:
            return
        
        send_mail(
            subject=notification.title,
            message=notification.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
