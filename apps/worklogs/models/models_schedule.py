"""
Report Schedule Model.

Allows clients to configure how often they want a progress report
for a given contract. The Celery Beat task `trigger_scheduled_reports`
checks this table daily and enqueues AI report generation when the
next_report_date has been reached.
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.bidding.models import Contract


class ReportSchedule(models.Model):
    """
    Client-configurable report schedule per contract.

    The client sets an interval (e.g., every 14 days) and the system
    automatically generates and delivers progress reports on that cadence
    — fully async via Celery, zero manual intervention required.

    Flow:
        1. Client creates/updates schedule via POST /api/worklogs/report-schedule/
        2. Celery Beat `trigger_scheduled_reports` runs daily at 00:05
        3. If next_report_date <= today, enqueue `generate_ai_report_task`
        4. Advance next_report_date by interval_days
        5. Freelancer notified 3 days before via `check_upcoming_report_deadlines`
    """

    class Interval(models.IntegerChoices):
        WEEKLY = 7, "Every 7 days (Weekly)"
        BIWEEKLY = 14, "Every 14 days (Biweekly)"
        MONTHLY = 30, "Every 30 days (Monthly)"

    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name="report_schedule",
        help_text="The contract this schedule belongs to",
    )
    interval_days = models.IntegerField(
        choices=Interval.choices,
        default=Interval.WEEKLY,
        help_text="How frequently to generate a progress report (7, 14, or 30 days)",
    )
    next_report_date = models.DateField(
        help_text="Date when the next progress report should be generated",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Pause/resume automatic report generation",
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_schedules_created",
        help_text="Client who configured this schedule",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "report_schedules"
        ordering = ["next_report_date"]
        indexes = [
            models.Index(fields=["next_report_date", "is_active"]),
        ]

    def __str__(self):
        return (
            f"Schedule for {self.contract.bid.project.title} "
            f"every {self.interval_days} days — next: {self.next_report_date}"
        )

    def advance_to_next(self) -> None:
        """
        Advance next_report_date by interval_days after a report is generated.
        Called by `trigger_scheduled_reports` Celery task after enqueueing report.
        """
        self.next_report_date = self.next_report_date + timedelta(days=self.interval_days)
        self.save(update_fields=["next_report_date", "updated_at"])

    @property
    def days_until_next_report(self) -> int:
        """Days remaining until the next scheduled report."""
        delta = self.next_report_date - timezone.localdate()
        return max(0, delta.days)

    @property
    def is_due_today(self) -> bool:
        """True if the report should be generated today or is overdue."""
        return self.next_report_date <= timezone.localdate()

    @property
    def is_upcoming_soon(self) -> bool:
        """True if the report is due within 3 days (triggers freelancer heads-up)."""
        return 0 < self.days_until_next_report <= 3
