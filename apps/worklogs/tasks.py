from celery import shared_task
from datetime import date, timedelta

from .models import WorkLog, WeeklyReport, DeliveryProof
from .ai_service import generate_weekly_report
from .pdf_service import generate_weekly_report_pdf, generate_delivery_proof_pdf


@shared_task
def generate_ai_report_task(contract_id: int, week_start: date):
    """
    Generate AI weekly report for a contract.
    Called by Celery Beat every Sunday.
    """
    # Generate report
    report = generate_weekly_report(contract_id, week_start)
    
    # Generate PDF
    generate_pdf_task.delay(report.id, 'weekly_report')
    
    # Notify freelancer
    notify_freelancer_report_ready.delay(report.id)


@shared_task
def generate_pdf_task(object_id: int, object_type: str):
    """
    Generate PDF for a report or proof.
    
    Args:
        object_id: ID of WeeklyReport or DeliveryProof
        object_type: 'weekly_report' or 'delivery_proof'
    """
    if object_type == 'weekly_report':
        pdf_url = generate_weekly_report_pdf(object_id)
    elif object_type == 'delivery_proof':
        pdf_url = generate_delivery_proof_pdf(object_id)
    else:
        raise ValueError(f"Unknown object_type: {object_type}")
    
    return pdf_url


@shared_task
def generate_proof_pdf_task(proof_id: int):
    """
    Generate PDF for delivery proof.
    """
    return generate_delivery_proof_pdf(proof_id)


@shared_task
def notify_freelancer_report_ready(report_id: int):
    """
    Notify freelancer that weekly report is ready.
    """
    from apps.notifications.services import create_notification
    
    try:
        report = WeeklyReport.objects.get(id=report_id)
        
        create_notification(
            recipient=report.contract.bid.freelancer,
            title="Weekly Report Ready",
            body=f"Your weekly report for {report.contract.bid.project.title} is ready for download.",
            type="REPORT_READY",
        )
    except WeeklyReport.DoesNotExist:
        pass


@shared_task
def notify_client_log_submitted(log_id: int):
    """
    Notify client that a work log was submitted.
    """
    from apps.notifications.services import create_notification
    
    try:
        log = WorkLog.objects.get(id=log_id)
        
        create_notification(
            recipient=log.contract.bid.project.client,
            title="New Work Log Submitted",
            body=f"{log.freelancer.get_full_name()} submitted a work log for {log.contract.bid.project.title}.",
            type="LOG_SUBMITTED",
        )
    except WorkLog.DoesNotExist:
        pass


@shared_task
def generate_weekly_reports_for_all_contracts():
    """
    Generate weekly reports for all active contracts.
    Called by Celery Beat every Sunday at 11:59 PM.
    """
    from apps.bidding.models import Contract
    
    # Get all active contracts
    active_contracts = Contract.objects.filter(is_active=True)
    
    # Calculate last week
    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    
    for contract in active_contracts:
        # Check if there are logs for last week
        logs_exist = WorkLog.objects.filter(
            contract=contract,
            date__range=[last_monday, last_monday + timedelta(days=6)]
        ).exists()
        
        if logs_exist:
            generate_ai_report_task.delay(contract.id, last_monday)
