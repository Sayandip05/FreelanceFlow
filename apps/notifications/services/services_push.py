"""Push notification service using Web Push."""
from django.conf import settings
import json


class PushNotificationService:
    """Service for sending web push notifications."""
    
    def __init__(self):
        self.enabled = getattr(settings, 'PUSH_NOTIFICATIONS_ENABLED', False)
        self.vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', '')
        self.vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', '')
        self.vapid_claims = getattr(settings, 'VAPID_CLAIMS', {})
    
    def send_push_notification(
        self,
        subscription_info: dict,
        title: str,
        body: str,
        data: dict = None,
        icon: str = None,
        badge: str = None,
    ) -> bool:
        """
        Send a push notification to a user's device.
        
        Args:
            subscription_info: Push subscription info from browser
            title: Notification title
            body: Notification body
            data: Additional data
            icon: Icon URL
            badge: Badge URL
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            from pywebpush import webpush, WebPushException
            
            payload = {
                'title': title,
                'body': body,
                'icon': icon or '/static/icons/notification-icon.png',
                'badge': badge or '/static/icons/badge-icon.png',
                'data': data or {},
            }
            
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims
            )
            
            return True
            
        except WebPushException as e:
            # Log error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Push notification failed: {str(e)}")
            return False
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Push notification error: {str(e)}")
            return False


# Global instance
push_service = PushNotificationService()


def send_push_to_user(user, title: str, body: str, data: dict = None):
    """
    Send push notification to a user.
    
    Args:
        user: User instance
        title: Notification title
        body: Notification body
        data: Additional data
    """
    from .models import PushSubscription
    
    # Get user's push subscriptions
    subscriptions = PushSubscription.objects.filter(
        user=user,
        is_active=True
    )
    
    for subscription in subscriptions:
        push_service.send_push_notification(
            subscription_info=subscription.subscription_data,
            title=title,
            body=body,
            data=data
        )
