"""Models for Payment Disputes."""
from django.db import models

from apps.users.models import User
from .models import Payment


class PaymentDispute(models.Model):
    """
    Payment dispute for a contract.
    Requires admin resolution.
    """
    
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"
    
    class Resolution(models.TextChoices):
        FAVOR_CLIENT = "FAVOR_CLIENT", "Favor Client"
        FAVOR_FREELANCER = "FAVOR_FREELANCER", "Favor Freelancer"
        SPLIT = "SPLIT", "Split Payment"
        REFUND = "REFUND", "Full Refund"
    
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name="dispute"
    )
    disputer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="disputes_initiated"
    )
    reason = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    
    # Resolution
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="disputes_resolved"
    )
    resolution = models.CharField(
        max_length=30,
        choices=Resolution.choices,
        null=True,
        blank=True
    )
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Evidence
    evidence_files = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "payment_disputes"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Dispute for Payment {self.payment.id} - {self.status}"


class DisputeMessage(models.Model):
    """
    Messages in a dispute thread.
    """
    
    dispute = models.ForeignKey(
        PaymentDispute,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    message = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "dispute_messages"
        ordering = ["created_at"]
    
    def __str__(self):
        return f"Message in Dispute {self.dispute.id} by {self.sender.email}"
