"""Extended worklog models - Time-off Tracking."""
from django.db import models
from apps.users.models import User
from apps.bidding.models import Contract


class TimeOff(models.Model):
    """
    Freelancer time-off/leave tracking.
    """
    
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
    
    class LeaveType(models.TextChoices):
        VACATION = "VACATION", "Vacation"
        SICK = "SICK", "Sick Leave"
        PERSONAL = "PERSONAL", "Personal"
        OTHER = "OTHER", "Other"
    
    freelancer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="time_offs"
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="time_offs",
        null=True,
        blank=True
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LeaveType.choices
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
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
        related_name="time_offs_approved"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "time_offs"
        ordering = ["-start_date"]
    
    def __str__(self):
        return f"{self.freelancer.email} - {self.leave_type} ({self.start_date} to {self.end_date})"
