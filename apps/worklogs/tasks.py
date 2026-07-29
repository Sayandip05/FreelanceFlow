"""
Celery background tasks for the worklogs app.

Task Architecture
-----------------
All tasks are intentionally async — no HTTP request ever blocks on these.

Queue routing (defined in config/celery.py):
  - HIGH priority:   payment tasks (see apps/payments/tasks.py)
  - DEFAULT:         notification tasks, log submitted
  - LOW priority:    PDF generation, AI report generation, scheduled reports

New Async Progress Report Flow
-------------------------------
Celery Beat fires two daily tasks:

1. check_upcoming_report_deadlines  — 9:00 AM daily
   For each active ReportSchedule due in ≤ 3 days:
   → notify_freelancer_report_upcoming.delay(schedule_id)
   (freelancer sees in-app alert: "Report due on <date>")

2. trigger_scheduled_reports        — 12:05 AM daily
   For each active ReportSchedule where next_report_date <= today:
   → generate_ai_report_task.delay(contract_id, week_start, interval_days)
   → schedule.advance_to_next()  [updates next_report_date in DB]

After AI report is generated:
   → generate_pdf_task.delay(report.id, 'weekly_report')
        └── WeasyPrint → PDF bytes → Azure Blob Storage → SAS URL
   → notify_freelancer_report_ready.delay(report.id)
   → notify_client_new_report.delay(report.id)
"""
from celery import shared_task
from datetime import date, timedelta

from apps.worklogs.models import WorkLog, WeeklyReport, DeliveryProof, ReportSchedule
from apps.worklogs.services.ai_service import generate_weekly_report
from apps.worklogs.services.pdf_service import generate_weekly_report_pdf, generate_delivery_proof_pdf


# ─────────────────────────────────────────────────────────────────────────────
# Core Report Generation
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 min before retry
    queue="freelanceflow_low_priority",
)
def generate_ai_report_task(self, contract_id: int, week_start_str: str, interval_days: int = 7):
    """
    Generate AI progress report for a contract.

    Called by:
    - `trigger_scheduled_reports` (automatic, via Celery Beat)
    - `ReportScheduleViewSet.generate_now` (manual trigger by client)

    Args:
        contract_id:    Contract ID
        week_start_str: ISO date string for the period start (YYYY-MM-DD)
        interval_days:  How many days this report covers (7, 14, or 30)
    """
    try:
        week_start = date.fromisoformat(week_start_str)

        # Generate AI report (LangGraph → Groq Llama 3.3 70B → WeeklyReport saved)
        report = generate_weekly_report(contract_id, week_start)

        # Record the interval that triggered this report
        report.interval_days = interval_days
        report.save(update_fields=["interval_days"])

        # Chain: PDF generation → notifications (all async)
        generate_pdf_task.delay(report.id, "weekly_report")
        notify_freelancer_report_ready.delay(report.id)
        notify_client_new_report.delay(report.id)

    except Exception as exc:
        # Retry up to 3 times with exponential back-off
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,  # 2 min before retry
    queue="freelanceflow_low_priority",
)
def generate_pdf_task(self, object_id: int, object_type: str):
    """
    Generate PDF for a report or delivery proof and upload to Azure Blob Storage.

    Args:
        object_id:   ID of WeeklyReport or DeliveryProof
        object_type: 'weekly_report' or 'delivery_proof'

    Returns:
        Azure Blob SAS URL of the generated PDF
    """
    try:
        if object_type == "weekly_report":
            return generate_weekly_report_pdf(object_id)
        elif object_type == "delivery_proof":
            return generate_delivery_proof_pdf(object_id)
        else:
            raise ValueError(f"Unknown object_type: {object_type!r}")
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(queue="freelanceflow_low_priority")
def generate_proof_pdf_task(proof_id: int):
    """Generate PDF for delivery proof and upload to Azure Blob Storage."""
    return generate_delivery_proof_pdf(proof_id)


# ─────────────────────────────────────────────────────────────────────────────
# Celery Beat — Scheduled Report Orchestration
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(queue="freelanceflow_low_priority")
def trigger_scheduled_reports():
    """
    Daily Celery Beat task (12:05 AM).

    Scans all active ReportSchedules. For any schedule where the
    next_report_date has arrived, enqueue an AI report generation task
    and advance the next_report_date by interval_days.

    Only generates a report if at least one WorkLog exists in the
    reporting period — avoids sending empty/useless reports.
    """
    today = date.today()

    due_schedules = ReportSchedule.objects.filter(
        is_active=True,
        next_report_date__lte=today,
        contract__is_active=True,
    ).select_related("contract__bid__project__client", "contract__bid__freelancer")

    triggered = 0
    for schedule in due_schedules:
        # Calculate the period this report covers
        period_end = today - timedelta(days=1)           # yesterday
        period_start = period_end - timedelta(days=schedule.interval_days - 1)

        # Only generate if logs exist — no empty reports
        has_logs = WorkLog.objects.filter(
            contract=schedule.contract,
            date__range=[period_start, period_end],
        ).exists()

        if has_logs:
            generate_ai_report_task.delay(
                schedule.contract.id,
                period_start.isoformat(),
                schedule.interval_days,
            )
            triggered += 1

        # Always advance the date, even if no logs exist (avoid stale queues)
        schedule.advance_to_next()

    return {"triggered": triggered, "total_due": due_schedules.count()}


@shared_task(queue="freelanceflow_low_priority")
def check_upcoming_report_deadlines():
    """
    Daily Celery Beat task (9:00 AM).

    Finds all active ReportSchedules where the report is due within
    3 days and fires a notification to the freelancer as a heads-up.

    Freelancer sees: "📋 Progress report due on <date> — make sure your
    work logs are up to date."
    """
    today = date.today()
    three_days_later = today + timedelta(days=3)

    upcoming_schedules = ReportSchedule.objects.filter(
        is_active=True,
        next_report_date__gt=today,
        next_report_date__lte=three_days_later,
        contract__is_active=True,
    ).select_related(
        "contract__bid__project",
        "contract__bid__freelancer",
    )

    for schedule in upcoming_schedules:
        notify_freelancer_report_upcoming.delay(schedule.id)

    return {"notified": upcoming_schedules.count()}


# ─────────────────────────────────────────────────────────────────────────────
# Notifications
# ─────────────────────────────────────────────────────────────────────────────

@shared_task
def notify_freelancer_report_ready(report_id: int):
    """
    Notify freelancer that a progress report has been generated.
    Called after AI report + PDF are complete.
    """
    from apps.notifications.services import notify_report_ready
    try:
        report = WeeklyReport.objects.select_related(
            "contract__bid__project",
            "contract__bid__freelancer",
        ).get(id=report_id)

        notify_report_ready(
            user=report.contract.bid.freelancer,
            project_title=report.contract.bid.project.title,
            week_str=f"{report.week_start} to {report.week_end}",
        )
    except WeeklyReport.DoesNotExist:
        pass


@shared_task
def notify_client_new_report(report_id: int):
    """
    Notify client that a new progress report PDF is available to view.
    Called after PDF has been uploaded to Azure Blob Storage.
    """
    from apps.notifications.services import notify_client_report_available
    try:
        report = WeeklyReport.objects.select_related(
            "contract__bid__project__client",
        ).get(id=report_id)

        notify_client_report_available(
            client=report.contract.bid.project.client,
            project_title=report.contract.bid.project.title,
            report_id=report.id,
        )

        # Mark as sent to client
        from django.utils import timezone
        report.sent_to_client_at = timezone.now()
        report.save(update_fields=["sent_to_client_at"])

    except WeeklyReport.DoesNotExist:
        pass


@shared_task
def notify_freelancer_report_upcoming(schedule_id: int):
    """
    Notify freelancer that an upcoming progress report is due within 3 days.
    Called by `check_upcoming_report_deadlines` Beat task.
    """
    from apps.notifications.services import notify_report_upcoming
    try:
        schedule = ReportSchedule.objects.select_related(
            "contract__bid__project",
            "contract__bid__freelancer",
        ).get(id=schedule_id)

        notify_report_upcoming(
            freelancer=schedule.contract.bid.freelancer,
            project_title=schedule.contract.bid.project.title,
            due_date=schedule.next_report_date.strftime("%B %d, %Y"),
        )
    except ReportSchedule.DoesNotExist:
        pass


@shared_task
def notify_client_log_submitted(log_id: int):
    """
    Notify client that a work log was submitted by the freelancer.
    """
    from apps.notifications.services import notify_log_submitted
    try:
        log = WorkLog.objects.select_related(
            "contract__bid__project__client",
        ).get(id=log_id)

        notify_log_submitted(
            client=log.contract.bid.project.client,
            project_title=log.contract.bid.project.title,
            date_str=str(log.date),
        )
    except WorkLog.DoesNotExist:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Legacy — All-Contracts Weekly Sweep (kept for backwards compatibility)
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(queue="freelanceflow_low_priority")
def generate_weekly_reports_for_all_contracts():
    """
    Legacy Beat task — Sunday 11:59 PM.

    Generates a weekly report for every active contract that has logs
    for the past week BUT does not yet have a ReportSchedule configured.

    Contracts WITH an active ReportSchedule are handled by
    `trigger_scheduled_reports` instead.
    """
    from apps.bidding.models import Contract

    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)

    # Only target contracts that have NOT been migrated to ReportSchedule
    active_contracts = Contract.objects.filter(
        is_active=True,
    ).exclude(report_schedule__is_active=True)

    triggered = 0
    for contract in active_contracts:
        has_logs = WorkLog.objects.filter(
            contract=contract,
            date__range=[last_monday, last_monday + timedelta(days=6)],
        ).exists()

        if has_logs:
            generate_ai_report_task.delay(
                contract.id,
                last_monday.isoformat(),
                7,  # default weekly interval
            )
            triggered += 1

    return {"triggered": triggered}
