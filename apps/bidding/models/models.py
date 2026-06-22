from django.db import models
from django.conf import settings

from apps.projects.models import Project


class Bid(models.Model):
    """
    Bid model for freelancers submitting proposals on projects.
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="bids"
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bids",
        limit_choices_to={'role': 'FREELANCER'}
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Bid amount for the project"
    )
    cover_letter = models.TextField(
        help_text="Proposal description"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "bids"
        ordering = ["-created_at"]
        unique_together = ["project", "freelancer"]
    
    def __str__(self):
        return f"Bid by {self.freelancer.email} on {self.project.title}"


class Contract(models.Model):
    """
    Contract model created when a bid is accepted.
    """
    bid = models.OneToOneField(
        Bid,
        on_delete=models.CASCADE,
        related_name="contract"
    )
    agreed_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "contracts"
        ordering = ["-start_date"]
    
    def __str__(self):
        return f"Contract for {self.bid.project.title}"
    
    @property
    def project(self):
        return self.bid.project
    
    @property
    def freelancer(self):
        return self.bid.freelancer
    
    @property
    def client(self):
        return self.bid.project.client
