import json
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from typing import List, Dict, Optional

from .models import WorkLog, WeeklyReport, DeliveryProof, Deliverable
from apps.bidding.models import Contract
from apps.users.models import User
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError
from core.utils import generate_report_id
from .groq_service import get_groq_service


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
    deliverables = Deliverable.objects.filter(contract=contract)
    
    total_hours = sum(log.hours_worked for log in logs)
    total_logs = logs.count()
    total_deliverables = deliverables.count()
    approved_deliverables = deliverables.filter(status=Deliverable.Status.APPROVED).count()
    
    with transaction.atomic():
        proof, created = DeliveryProof.objects.update_or_create(
            contract=contract,
            defaults={
                'total_hours': total_hours,
                'total_logs_count': total_logs,
                'total_deliverables': total_deliverables,
                'approved_deliverables': approved_deliverables,
                'report_id': generate_report_id(),
            }
        )
        
        # Generate PDF asynchronously
        transaction.on_commit(
            lambda: generate_proof_pdf_task.delay(proof.id)
        )
        
        return proof


# ============================================================================
# DELIVERABLE SERVICES - AI-Powered Worklog Flow
# ============================================================================

def create_deliverable_draft(
    freelancer,
    contract_id: int,
    title: str,
    description: str,
    ai_chat_transcript: List[Dict],
    ai_generated_report: str,
    hours_logged: float,
    attached_files: List[str] = None,
) -> Deliverable:
    """
    Create a new deliverable draft from AI chat conversation.
    
    Args:
        freelancer: User instance (must be freelancer)
        contract_id: Contract ID
        title: Deliverable title
        description: Description of work completed
        ai_chat_transcript: Full chat conversation with AI
        ai_generated_report: AI-generated structured report
        hours_logged: Hours associated with this work
        attached_files: List of file URLs
    
    Returns:
        Created Deliverable instance
    """
    if freelancer.role != User.Roles.FREELANCER:
        raise PermissionDeniedError("Only freelancers can create deliverables.")
    
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise NotFoundError("Contract not found.")
    
    # Verify freelancer is assigned to contract
    if contract.bid.freelancer != freelancer:
        raise PermissionDeniedError("You are not assigned to this contract.")
    
    # Check contract is active
    if not contract.is_active:
        raise ValidationError("Contract is not active.")
    
    # Validate hours
    if hours_logged <= 0 or hours_logged > 24:
        raise ValidationError("Hours must be between 0 and 24.", field="hours_logged")
    
    with transaction.atomic():
        deliverable = Deliverable.objects.create(
            contract=contract,
            freelancer=freelancer,
            title=title,
            description=description,
            ai_chat_transcript=ai_chat_transcript,
            ai_generated_report=ai_generated_report,
            hours_logged=hours_logged,
            attached_files=attached_files or [],
            status=Deliverable.Status.DRAFT,
        )
        
        return deliverable


def submit_deliverable_for_review(deliverable: Deliverable, freelancer) -> Deliverable:
    """
    Submit a deliverable draft for client review.
    
    Args:
        deliverable: Deliverable instance
        freelancer: User instance (must be owner)
    
    Returns:
        Updated Deliverable instance
    """
    if deliverable.freelancer != freelancer:
        raise PermissionDeniedError("You can only submit your own deliverables.")
    
    if deliverable.status != Deliverable.Status.DRAFT:
        raise ValidationError("Only draft deliverables can be submitted.")
    
    deliverable.status = Deliverable.Status.SUBMITTED
    deliverable.submitted_at = timezone.now()
    deliverable.save()
    
    # Notify client
    from apps.notifications.services import create_notification
    create_notification(
        recipient=deliverable.contract.bid.project.client,
        title="New Deliverable Submitted",
        body=f"{freelancer.get_full_name()} submitted '{deliverable.title}' for review.",
        type="DELIVERABLE_SUBMITTED",
        data={"deliverable_id": deliverable.id, "contract_id": deliverable.contract.id}
    )
    
    return deliverable


def approve_deliverable(
    deliverable: Deliverable, 
    client,
    feedback: str = ""
) -> Deliverable:
    """
    Approve a deliverable and optionally release payment.
    This is the key step in the approval flow.
    
    Args:
        deliverable: Deliverable instance
        client: User instance (must be contract client)
        feedback: Optional feedback message
    
    Returns:
        Updated Deliverable instance
    """
    if deliverable.contract.bid.project.client != client:
        raise PermissionDeniedError("Only the client can approve deliverables.")
    
    if deliverable.status not in [Deliverable.Status.SUBMITTED, Deliverable.Status.UNDER_REVIEW]:
        raise ValidationError("Deliverable is not pending approval.")
    
    with transaction.atomic():
        deliverable.status = Deliverable.Status.APPROVED
        deliverable.client_feedback = feedback
        deliverable.reviewed_by = client
        deliverable.reviewed_at = timezone.now()
        deliverable.save()
        
        # Create an associated WorkLog for tracking
        WorkLog.objects.create(
            contract=deliverable.contract,
            freelancer=deliverable.freelancer,
            date=timezone.now().date(),
            description=deliverable.ai_generated_report or deliverable.description,
            hours_worked=deliverable.hours_logged,
            status=WorkLog.Status.APPROVED,
            approved_at=timezone.now(),
            approved_by=client,
            ai_generated_summary=deliverable.ai_generated_report,
        )
        
        # Notify freelancer
        from apps.notifications.services import create_notification
        create_notification(
            recipient=deliverable.freelancer,
            title="Deliverable Approved",
            body=f"Your deliverable '{deliverable.title}' has been approved!",
            type="DELIVERABLE_APPROVED",
            data={"deliverable_id": deliverable.id}
        )
        
        return deliverable


def reject_deliverable(
    deliverable: Deliverable,
    client,
    feedback: str,
    request_revision: bool = True
) -> Deliverable:
    """
    Reject or request revision for a deliverable.
    
    Args:
        deliverable: Deliverable instance
        client: User instance (must be contract client)
        feedback: Required feedback explaining rejection
        request_revision: If True, status becomes REVISION_REQUESTED
    
    Returns:
        Updated Deliverable instance
    """
    if deliverable.contract.bid.project.client != client:
        raise PermissionDeniedError("Only the client can reject deliverables.")
    
    if deliverable.status not in [Deliverable.Status.SUBMITTED, Deliverable.Status.UNDER_REVIEW]:
        raise ValidationError("Deliverable is not pending approval.")
    
    if not feedback:
        raise ValidationError("Feedback is required when rejecting a deliverable.", field="feedback")
    
    deliverable.status = (
        Deliverable.Status.REVISION_REQUESTED 
        if request_revision 
        else Deliverable.Status.REJECTED
    )
    deliverable.client_feedback = feedback
    deliverable.reviewed_by = client
    deliverable.reviewed_at = timezone.now()
    deliverable.save()
    
    # Notify freelancer
    from apps.notifications.services import create_notification
    create_notification(
        recipient=deliverable.freelancer,
        title="Revision Requested" if request_revision else "Deliverable Rejected",
        body=f"Client has requested changes to '{deliverable.title}'.",
        type="DELIVERABLE_REVISION_REQUESTED",
        data={"deliverable_id": deliverable.id}
    )
    
    return deliverable


def update_deliverable_draft(
    deliverable: Deliverable,
    freelancer,
    title: str = None,
    description: str = None,
    hours_logged: float = None,
    attached_files: List[str] = None,
) -> Deliverable:
    """
    Update a deliverable draft.
    
    Args:
        deliverable: Deliverable instance
        freelancer: User instance (must be owner)
        title: New title (optional)
        description: New description (optional)
        hours_logged: New hours (optional)
        attached_files: New files (optional)
    
    Returns:
        Updated Deliverable instance
    """
    if deliverable.freelancer != freelancer:
        raise PermissionDeniedError("You can only update your own deliverables.")
    
    if deliverable.status not in [Deliverable.Status.DRAFT, Deliverable.Status.REVISION_REQUESTED]:
        raise ValidationError("Cannot update a submitted deliverable.")
    
    if title is not None:
        deliverable.title = title
    if description is not None:
        deliverable.description = description
    if hours_logged is not None:
        if hours_logged <= 0 or hours_logged > 24:
            raise ValidationError("Hours must be between 0 and 24.", field="hours_logged")
        deliverable.hours_logged = hours_logged
    if attached_files is not None:
        deliverable.attached_files = attached_files
    
    # If it was rejected/revision requested, put back to draft
    if deliverable.status == Deliverable.Status.REVISION_REQUESTED:
        deliverable.status = Deliverable.Status.DRAFT
        deliverable.revision_notes = deliverable.client_feedback
        deliverable.client_feedback = ""
    
    deliverable.save()
    return deliverable


# ============================================================================
# AI CHAT SERVICES
# ============================================================================

def process_ai_chat_message(
    contract_id: int,
    message: str,
    chat_history: List[Dict[str, str]],
    project_name: str
) -> Dict:
    """
    Process a message in the AI chat and get response.
    
    Args:
        contract_id: Contract ID for context
        message: User's message
        chat_history: Previous messages in the conversation
        project_name: Name of the project
    
    Returns:
        Dict with AI response and report status
    """
    service = get_groq_service()
    
    # Add user message to history
    messages = chat_history + [{"role": "user", "content": message}]
    
    # Get AI response
    response = service.chat(messages, project_name)
    
    return response


def generate_deliverable_from_chat(
    chat_transcript: List[Dict[str, str]],
    project_name: str,
    contract_id: int,
    freelancer,
    attached_files: List[str] = None
) -> Deliverable:
    """
    Generate a complete deliverable from an AI chat conversation.
    
    Args:
        chat_transcript: Full chat conversation
        project_name: Name of the project
        contract_id: Contract ID
        freelancer: User instance
        attached_files: List of uploaded file URLs
    
    Returns:
        Created Deliverable instance
    """
    service = get_groq_service()
    
    # Generate structured report from chat
    report_data = service.generate_worklog_from_chat(chat_transcript, project_name)
    
    # Create deliverable
    deliverable = create_deliverable_draft(
        freelancer=freelancer,
        contract_id=contract_id,
        title=report_data.get("title", "Work Submission"),
        description=report_data.get("description", ""),
        ai_chat_transcript=chat_transcript,
        ai_generated_report=json.dumps(report_data),
        hours_logged=report_data.get("hours_worked", 0),
        attached_files=attached_files or [],
    )
    
    return deliverable
