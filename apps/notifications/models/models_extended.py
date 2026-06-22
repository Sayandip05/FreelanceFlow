"""Extended notification models - Digest Emails, System Announcements."""
from django.db import models
from apps.users.models import User


class DigestEmail(models.Model):
    """
    Weekly digest email tracking.
    """
    
    class Frequency(models.TextChoices):
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="digest_emails"
    )
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.WEEKLY
    )
    content = models.JSONField(default=dict)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "digest_emails"
        ordering = ["-sent_at"]
    
    def __str__(self):
        return f"Digest for {self.user.email} - {self.sent_at}"


class SystemAnnouncement(models.Model):
    """
    Platform-wide system announcements.
    """
    
    class AnnouncementType(models.TextChoices):
        INFO = "INFO", "Information"
        WARNING = "WARNING", "Warning"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        FEATURE = "FEATURE", "New Feature"
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    announcement_type = models.CharField(
        max_length=20,
        choices=AnnouncementType.choices,
        default=AnnouncementType.INFO
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    target_users = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Users'),
            ('freelancers', 'Freelancers Only'),
            ('clients', 'Clients Only')
        ],
        default='all'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="announcements_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "system_announcements"
        ordering = ["-start_date"]
    
    def __str__(self):
        return f"{self.title} - {self.announcement_type}"
