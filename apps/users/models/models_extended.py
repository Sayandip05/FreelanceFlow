"""Extended user models - Activity Logging, Online Status."""
from django.db import models
from apps.users.models import User


class ActivityLog(models.Model):
    """
    Audit log for user activities.
    """
    
    class ActionType(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        PROJECT_CREATED = "PROJECT_CREATED", "Project Created"
        BID_PLACED = "BID_PLACED", "Bid Placed"
        CONTRACT_SIGNED = "CONTRACT_SIGNED", "Contract Signed"
        PAYMENT_MADE = "PAYMENT_MADE", "Payment Made"
        REVIEW_POSTED = "REVIEW_POSTED", "Review Posted"
        PROFILE_UPDATED = "PROFILE_UPDATED", "Profile Updated"
        PASSWORD_CHANGED = "PASSWORD_CHANGED", "Password Changed"
        OTHER = "OTHER", "Other"
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="activity_logs"
    )
    action_type = models.CharField(
        max_length=50,
        choices=ActionType.choices
    )
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "activity_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="act_log_user_created_idx"),
            models.Index(fields=["action_type"], name="act_log_action_type_idx"),
            models.Index(fields=["user", "action_type", "-created_at"], name="act_log_user_action_idx"),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action_type} at {self.created_at}"


class UserOnlineStatus(models.Model):
    """
    Track user online/offline status.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="online_status"
    )
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_online_status"
        indexes = [
            models.Index(
                fields=['is_online', 'last_seen'],
                name='user_presence_idx'
            ),
        ]
    
    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        return f"{self.user.email} - {status}"
