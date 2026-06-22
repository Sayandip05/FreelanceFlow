"""Models for Contract Termination."""
from django.db import models

from apps.users.models import User
from .models import Contract


class ContractTerminationRequest(models.Model):
    """
    Request to terminate a contract early.
    Requires approval from the other party.
    """
    
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
    
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name="termination_request"
    )
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="termination_requests_made"
    )
    reason = models.CharField(max_length=100)
    explanation = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Approval/Rejection
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="termination_requests_approved"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    refund_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Percentage of escrow to refund to client"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "contract_termination_requests"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Termination request for Contract {self.contract.id} - {self.status}"
