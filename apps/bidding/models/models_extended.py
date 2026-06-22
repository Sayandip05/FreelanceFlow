"""Extended bidding models - Bid Retraction, Counter-Offers."""
from django.db import models
from apps.users.models import User
from .models import Bid, Contract


class BidRetraction(models.Model):
    """
    Bid retraction before deadline.
    """
    bid = models.OneToOneField(
        Bid,
        on_delete=models.CASCADE,
        related_name="retraction"
    )
    reason = models.TextField()
    retracted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "bid_retractions"
    
    def __str__(self):
        return f"Retraction for Bid {self.bid.id}"


class CounterOffer(models.Model):
    """
    Client counter-offer on a bid.
    """
    
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        EXPIRED = "EXPIRED", "Expired"
    
    bid = models.ForeignKey(
        Bid,
        on_delete=models.CASCADE,
        related_name="counter_offers"
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="counter_offers_made"
    )
    proposed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    proposed_deadline = models.DateField(null=True, blank=True)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "counter_offers"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Counter-offer for Bid {self.bid.id} - {self.status}"


class WorklogApproval(models.Model):
    """
    Client approval for freelancer worklogs.
    """
    
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
    
    worklog = models.OneToOneField(
        'worklogs.WorkLog',
        on_delete=models.CASCADE,
        related_name="approval"
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="worklog_approvals"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    feedback = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "worklog_approvals"
    
    def __str__(self):
        return f"Approval for Worklog {self.worklog.id} - {self.status}"
