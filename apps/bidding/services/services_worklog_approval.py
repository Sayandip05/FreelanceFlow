"""
Worklog Approval Services
Allows clients to approve/reject freelancer worklogs
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.worklogs.models import WorkLog
from .models_extended import WorklogApproval


@transaction.atomic
def submit_worklog_for_approval(worklog_id, freelancer):
    """
    Submit a worklog for client approval
    
    Args:
        worklog_id: ID of the worklog
        freelancer: User instance (must be worklog owner)
    
    Returns:
        WorklogApproval instance
    
    Raises:
        ValidationError: If worklog cannot be submitted
    """
    try:
        worklog = WorkLog.objects.select_related('contract').get(id=worklog_id)
    except WorkLog.DoesNotExist:
        raise ValidationError("Worklog not found")
    
    # Verify ownership
    if worklog.freelancer != freelancer:
        raise ValidationError("You can only submit your own worklogs")
    
    # Check if already submitted
    if WorklogApproval.objects.filter(worklog=worklog).exists():
        raise ValidationError("Worklog already submitted for approval")
    
    # Create approval request
    approval = WorklogApproval.objects.create(
        worklog=worklog,
        approved_by=worklog.contract.bid.project.client,  # Client who posted the project
        status=WorklogApproval.Status.PENDING
    )
    
    return approval


@transaction.atomic
def approve_worklog(approval_id, client, feedback=None):
    """
    Approve a worklog
    
    Args:
        approval_id: ID of the approval request
        client: User instance (must be project owner)
        feedback: Optional feedback message
    
    Returns:
        WorklogApproval instance
    
    Raises:
        ValidationError: If worklog cannot be approved
    """
    try:
        approval = WorklogApproval.objects.select_related(
            'worklog', 'worklog__contract', 'worklog__contract__bid', 'worklog__contract__bid__project'
        ).get(id=approval_id)
    except WorklogApproval.DoesNotExist:
        raise ValidationError("Approval request not found")
    
    # Verify client is project owner
    if approval.worklog.contract.bid.project.client != client:
        raise ValidationError("Only project owner can approve worklogs")
    
    # Check status
    if approval.status != WorklogApproval.Status.PENDING:
        raise ValidationError(f"Approval status is {approval.status}")
    
    # Update approval
    approval.status = WorklogApproval.Status.APPROVED
    approval.feedback = feedback
    approval.approved_at = timezone.now()
    approval.save()
    
    # Update worklog status
    worklog = approval.worklog
    worklog.status = WorkLog.Status.APPROVED
    worklog.save()
    
    return approval


@transaction.atomic
def reject_worklog(approval_id, client, feedback):
    """
    Reject a worklog
    
    Args:
        approval_id: ID of the approval request
        client: User instance (must be project owner)
        feedback: Rejection feedback (required)
    
    Returns:
        WorklogApproval instance
    
    Raises:
        ValidationError: If worklog cannot be rejected
    """
    if not feedback:
        raise ValidationError("Feedback is required when rejecting a worklog")
    
    try:
        approval = WorklogApproval.objects.select_related(
            'worklog', 'worklog__contract', 'worklog__contract__bid', 'worklog__contract__bid__project'
        ).get(id=approval_id)
    except WorklogApproval.DoesNotExist:
        raise ValidationError("Approval request not found")
    
    # Verify client is project owner
    if approval.worklog.contract.bid.project.client != client:
        raise ValidationError("Only project owner can reject worklogs")
    
    # Check status
    if approval.status != WorklogApproval.Status.PENDING:
        raise ValidationError(f"Approval status is {approval.status}")
    
    # Update approval
    approval.status = WorklogApproval.Status.REJECTED
    approval.feedback = feedback
    approval.save()
    
    # Update worklog status
    worklog = approval.worklog
    worklog.status = WorkLog.Status.REJECTED
    worklog.save()
    
    return approval


def get_pending_approvals(client, limit=50):
    """Get pending worklog approvals for a client"""
    return WorklogApproval.objects.filter(
        approved_by=client,
        status=WorklogApproval.Status.PENDING
    ).select_related('worklog', 'worklog__freelancer', 'worklog__contract').order_by('-created_at')[:limit]


def get_worklog_approval_status(worklog_id):
    """Get approval status for a worklog"""
    try:
        approval = WorklogApproval.objects.get(worklog_id=worklog_id)
        return {
            'status': approval.status,
            'feedback': approval.feedback,
            'approved_at': approval.approved_at,
            'created_at': approval.created_at
        }
    except WorklogApproval.DoesNotExist:
        return None


def get_approval_stats(contract_id):
    """
    Get worklog approval statistics for a contract
    
    Returns:
        Dict with approved/rejected/pending counts
    """
    from django.db.models import Count, Q
    
    stats = WorklogApproval.objects.filter(
        worklog__contract_id=contract_id
    ).aggregate(
        total=Count('id'),
        approved=Count('id', filter=Q(status=WorklogApproval.Status.APPROVED)),
        rejected=Count('id', filter=Q(status=WorklogApproval.Status.REJECTED)),
        pending=Count('id', filter=Q(status=WorklogApproval.Status.PENDING))
    )
    
    return stats
