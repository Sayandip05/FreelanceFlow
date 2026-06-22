from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    In-app notifications for users.
    """
    class Type(models.TextChoices):
        BID_SUBMITTED = "BID_SUBMITTED", "Bid Submitted"
        BID_ACCEPTED = "BID_ACCEPTED", "Bid Accepted"
        ESCROW_CREATED = "ESCROW_CREATED", "Escrow Created"
        LOG_SUBMITTED = "LOG_SUBMITTED", "Log Submitted"
        REPORT_READY = "REPORT_READY", "Report Ready"
        PAYMENT_RELEASED = "PAYMENT_RELEASED", "Payment Released"
        PROOF_READY = "PROOF_READY", "Proof Ready"
        MESSAGE_RECEIVED = "MESSAGE_RECEIVED", "Message Received"
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    type = models.CharField(max_length=50, choices=Type.choices)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]
    
    def __str__(self):
        return f"{self.type} to {self.recipient.email}"
