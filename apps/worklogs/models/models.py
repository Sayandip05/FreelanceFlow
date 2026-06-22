from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.bidding.models import Contract


class WorkLog(models.Model):
    """
    Daily work log submitted by freelancers.
    """
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="work_logs"
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="work_logs"
    )
    date = models.DateField()
    description = models.TextField(help_text="What was done today")
    hours_worked = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Hours worked (e.g., 7.5)",
        validators=[MinValueValidator(0.1), MaxValueValidator(24)]
    )
    screenshot = models.ImageField(
        upload_to='worklogs/screenshots/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Screenshot proof of work"
    )
    screenshot_url = models.URLField(
        blank=True,
        help_text="Optional screenshot URL (legacy)"
    )
    reference_url = models.URLField(
        blank=True,
        help_text="Optional reference link (GitHub, Figma, etc.)"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    ai_generated_summary = models.TextField(
        blank=True,
        help_text="AI-generated summary from chat conversation"
    )
    client_notes = models.TextField(
        blank=True,
        help_text="Client feedback/notes on the work log"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_work_logs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "work_logs"
        ordering = ["-date", "-created_at"]
        unique_together = ["contract", "date"]
    
    def __str__(self):
        return f"Log for {self.contract.bid.project.title} on {self.date}"
    
    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED
    
    @property
    def is_pending(self):
        return self.status == self.Status.PENDING_APPROVAL


class WeeklyReport(models.Model):
    """
    AI-generated weekly progress report.
    """
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="weekly_reports"
    )
    week_start = models.DateField()
    week_end = models.DateField()
    ai_summary = models.TextField(help_text="AI-generated report content")
    pdf_url = models.URLField(
        blank=True,
        help_text="S3 URL to generated PDF"
    )
    sent_to_client_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "weekly_reports"
        ordering = ["-week_start"]
        unique_together = ["contract", "week_start"]
    
    def __str__(self):
        return f"Report for week {self.week_start} to {self.week_end}"
    
    @property
    def total_hours(self):
        """Calculate total hours for this week."""
        from django.db.models import Sum
        result = WorkLog.objects.filter(
            contract=self.contract,
            date__range=[self.week_start, self.week_end]
        ).aggregate(total=Sum('hours_worked'))
        return result['total'] or 0


class Deliverable(models.Model):
    """
    A deliverable item submitted by freelancer for client approval.
    This is the core of the AI-powered worklog flow.
    """
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted for Review"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        REVISION_REQUESTED = "REVISION_REQUESTED", "Revision Requested"
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="deliverables"
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submitted_deliverables"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Description of what was accomplished")
    ai_chat_transcript = models.JSONField(
        default=list,
        help_text="Full chat conversation with AI"
    )
    ai_generated_report = models.TextField(
        blank=True,
        help_text="AI-generated report from chat conversation"
    )
    attached_files = models.JSONField(
        default=list,
        help_text="List of attached file URLs"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_deliverables"
    )
    client_feedback = models.TextField(blank=True)
    revision_notes = models.TextField(blank=True)
    hours_logged = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Hours associated with this deliverable"
    )
    payment_released = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "deliverables"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Deliverable: {self.title} ({self.status})"


class DeliveryProof(models.Model):
    """
    Final proof of delivery document generated at project completion.
    """
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name="delivery_proof"
    )
    pdf_url = models.URLField(
        help_text="S3 URL to generated PDF"
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    total_hours = models.DecimalField(max_digits=10, decimal_places=2)
    total_logs_count = models.IntegerField()
    total_deliverables = models.IntegerField(default=0)
    approved_deliverables = models.IntegerField(default=0)
    report_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique tamper-evident report ID"
    )
    
    class Meta:
        db_table = "delivery_proofs"
    
    def __str__(self):
        return f"Proof for {self.contract.bid.project.title}"
