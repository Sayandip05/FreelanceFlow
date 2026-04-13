"""Models for Contract Amendments."""
from django.db import models
from django.core.validators import MinValueValidator

from apps.users.models import User
from .models import Contract


class ContractAmendment(models.Model):
    """
    Contract amendment for scope/budget changes.
    Requires approval from both parties.
    """
    
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
    
    class AmendmentType(models.TextChoices):
        SCOPE_CHANGE = "SCOPE_CHANGE", "Scope Change"
        BUDGET_CHANGE = "BUDGET_CHANGE", "Budget Change"
        DEADLINE_CHANGE = "DEADLINE_CHANGE", "Deadline Change"
        COMBINED = "COMBINED", "Combined Changes"
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="amendments"
    )
    proposed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="amendments_proposed"
    )
    amendment_type = models.CharField(
        max_length=20,
        choices=AmendmentType.choices
    )
    
    # Changes
    new_scope = models.TextField(blank=True, help_text="New scope description")
    new_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    new_deadline = models.DateField(null=True, blank=True)
    reason = models.TextField(help_text="Reason for amendment")
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="amendments_approved"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "contract_amendments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["contract", "status"]),
            models.Index(fields=["proposed_by"]),
        ]
    
    def __str__(self):
        return f"Amendment for Contract {self.contract.id} - {self.status}"
