"""Models for Push Notifications."""
from django.db import models
from apps.users.models import User


class PushSubscription(models.Model):
    """
    Store user's push notification subscriptions.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="push_subscriptions"
    )
    subscription_data = models.JSONField(
        help_text="Push subscription info from browser"
    )
    device_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "push_subscriptions"
        unique_together = ["user", "subscription_data"]
    
    def __str__(self):
        return f"Push subscription for {self.user.email}"


class NotificationPreference(models.Model):
    """
    User preferences for notifications.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_preferences"
    )
    
    # Email preferences
    email_bid_received = models.BooleanField(default=True)
    email_bid_accepted = models.BooleanField(default=True)
    email_payment_released = models.BooleanField(default=True)
    email_deliverable_submitted = models.BooleanField(default=True)
    email_review_received = models.BooleanField(default=True)
    email_contract_termination = models.BooleanField(default=True)
    email_dispute = models.BooleanField(default=True)
    email_message = models.BooleanField(default=True)
    
    # Push preferences
    push_bid_received = models.BooleanField(default=True)
    push_bid_accepted = models.BooleanField(default=True)
    push_payment_released = models.BooleanField(default=True)
    push_deliverable_submitted = models.BooleanField(default=True)
    push_review_received = models.BooleanField(default=True)
    push_contract_termination = models.BooleanField(default=True)
    push_dispute = models.BooleanField(default=True)
    push_message = models.BooleanField(default=True)
    
    # In-app preferences
    inapp_all = models.BooleanField(default=True)
    
    # Digest emails
    weekly_digest = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "notification_preferences"
    
    def __str__(self):
        return f"Notification preferences for {self.user.email}"
