from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta

from .models import WorkLog, WeeklyReport, DeliveryProof
from apps.bidding.models import Contract
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError
from core.utils import generate_report_id


def create_worklog(
    freelancer,
    contract_id: int,
    log_date: date,
    description: str,
    hours_worked: float,
    screenshot_url: str = "",
    reference_url: str = "",
) -> WorkLog:
    """
    Create a daily work log.
    
    Args:
        freelancer: User instance (must be freelancer)
        contract_id: Contract ID
        log_date: Date of work
        description: What was done
        hours_worked: Hours worked
        screenshot_url: Optional screenshot URL
        reference_url: Optional reference URL
    
    Returns:
        Created WorkLog instance
    """
    from apps.users.models import User
    
    if freelancer.role != User.Roles.FREELANCER:
        raise PermissionDeniedError("Only freelancers can create work logs.")
    
    # Get contract
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise NotFoundError("Contract not found.")
    
    # Verify freelancer is assigned to contract
    if contract.bid.freelancer != freelancer:
        raise PermissionDeniedError(
            "You are not assigned to this contract."
        )
    
    # Check contract is active
    if not contract.is_active:
        raise ValidationError("Contract is not active.")
    
    # Validate one log per day
    if WorkLog.objects.filter(contract=contract, date=log_date).exists():
        raise ValidationError(
            "Work log already exists for this date.",
            field="date"
        )
    
    # Validate hours
    if hours_worked <= 0 or hours_worked > 24:
        raise ValidationError(
            "Hours must be between 0 and 24.",
            field="hours_worked"
        )
    
    # Validate description
    if not description or len(description.strip()) < 10:
        raise ValidationError(
            "Description must be at least 10 characters.",
            field="description"
        )
    
    with transaction.atomic():
        log = WorkLog.objects.create(
            contract=contract,
            freelancer=freelancer,
            date=log_date,
            description=description,
            hours_worked=hours_worked,
            screenshot_url=screenshot_url,
            reference_url=reference_url,
        )
        
        # Schedule notification to client
        transaction.on_commit(
            lambda: notify_client_log_submitted.delay(log.id)
        )
        
        return log


def update_worklog(
    log: WorkLog,
    freelancer,
    description: str | None = None,
    hours_worked: float | None = None,
    screenshot_url: str | None = None,
    reference_url: str | None = None,
) -> WorkLog:
    """
    Update a work log.
    """
    if log.freelancer != freelancer:
        raise PermissionDeniedError("You can only update your own logs.")
    
    if description is not None:
        if len(description.strip()) < 10:
            raise ValidationError(
                "Description must be at least 10 characters.",
                field="description"
            )
        log.description = description
    
    if hours_worked is not None:
        if hours_worked <= 0 or hours_worked > 24:
            raise ValidationError(
                "Hours must be between 0 and 24.",
                field="hours_worked"
            )
        log.hours_worked = hours_worked
    
    if screenshot_url is not None:
        log.screenshot_url = screenshot_url
    
    if reference_url is not None:
        log.reference_url = reference_url
    
    log.save()
    return log


def delete_worklog(log: WorkLog, freelancer) -> None:
    """Delete a work log."""
    if log.freelancer != freelancer:
        raise PermissionDeniedError("You can only delete your own logs.")
    
    log.delete()


def generate_delivery_proof(contract_id: int) -> DeliveryProof:
    """
    Generate final proof of delivery document.
    Called when project is completed.
    """
    from .tasks import generate_proof_pdf_task
    
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise NotFoundError("Contract not found.")
    
    # Get all logs and reports
    logs = WorkLog.objects.filter(contract=contract)
    reports = WeeklyReport.objects.filter(contract=contract)
    
    total_hours = sum(log.hours_worked for log in logs)
    total_logs = logs.count()
    
    with transaction.atomic():
        proof, created = DeliveryProof.objects.update_or_create(
            contract=contract,
            defaults={
                'total_hours': total_hours,
                'total_logs_count': total_logs,
                'report_id': generate_report_id(),
            }
        )
        
        # Generate PDF asynchronously
        transaction.on_commit(
            lambda: generate_proof_pdf_task.delay(proof.id)
        )
        
        return proof
