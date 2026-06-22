"""Models for Milestone-based Payments."""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.bidding.models import Contract
from apps.users.models import User


class PaymentMilestone(models.Model):
    """
    Payment milestone for breaking payments into stages.
    """
    
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        SUBMITTED = "SUBMITTED", "Submitted for Review"
        APPROVED = "APPROVED", "Approved"
        PAID = "PAID", "Paid"
        REJECTED = "REJECTED", "Rejected"
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="milestones"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of total contract amount"
    )
    order = models.IntegerField(
        default=1,
        help_text="Order of milestone in sequence"
    )
    
    # Deliverables
    deliverable_description = models.TextField(blank=True)
    deliverable_files = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Dates
    due_date = models.DateField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Review
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="milestones_approved"
    )
    client_feedback = models.TextField(blank=True)
    
    # Payment
    payment_id = models.CharField(max_length=255, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "payment_milestones"
        ordering = ["contract", "order"]
        unique_together = ["contract", "order"]
        indexes = [
            models.Index(fields=["contract", "status"]),
            models.Index(fields=["status"]),
        ]
    
    def __str__(self):
        return f"Milestone {self.order}: {self.title} - {self.status}"
