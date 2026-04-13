"""Services for Contract Amendments."""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import Contract
from .models_amendment import ContractAmendment
from apps.users.models import User
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError


def propose_contract_amendment(
    contract_id: int,
    proposer: User,
    amendment_type: str,
    reason: str,
    new_scope: str = None,
    new_budget: Decimal = None,
    new_deadline = None,
) -> ContractAmendment:
    """
    Propose a contract amendment.
    
    Args:
        contract_id: Contract ID
        proposer: User proposing the amendment
        amendment_type: Type of amendment
        reason: Reason for amendment
        new_scope: New scope description (optional)
        new_budget: New budget amount (optional)
        new_deadline: New deadline date (optional)
    
    Returns:
        Created ContractAmendment instance
    """
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise NotFoundError("Contract not found.")
    
    # Verify proposer is part of contract
    if proposer not in [contract.bid.freelancer, contract.bid.project.client]:
        raise PermissionDeniedError("You are not part of this contract.")
    
    # Check contract is active
    if not contract.is_active:
        raise ValidationError("Contract is not active.")
    
    # Validate at least one change is provided
    if not any([new_scope, new_budget, new_deadline]):
        raise ValidationError("At least one change must be specified.")
    
    with transaction.atomic():
        amendment = ContractAmendment.objects.create(
            contract=contract,
            proposed_by=proposer,
            amendment_type=amendment_type,
            new_scope=new_scope or "",
            new_budget=new_budget,
            new_deadline=new_deadline,
            reason=reason,
            status=ContractAmendment.Status.PENDING,
        )
        
        # Notify the other party
        other_party = (
            contract.bid.project.client 
            if proposer == contract.bid.freelancer 
            else contract.bid.freelancer
        )
        
        from apps.notifications.services import create_notification
        create_notification(
            recipient=other_party,
            title="Contract Amendment Proposed",
            body=f"{proposer.get_full_name()} has proposed a contract amendment.",
            type="CONTRACT_AMENDMENT_PROPOSED",
            data={
                "contract_id": contract.id,
                "amendment_id": amendment.id
            }
        )
        
        return amendment


def approve_contract_amendment(
    amendment_id: int,
    approver: User,
) -> ContractAmendment:
    """
    Approve a contract amendment.
    
    Args:
        amendment_id: Amendment ID
        approver: User approving the amendment
    
    Returns:
        Updated ContractAmendment instance
    """
    try:
        amendment = ContractAmendment.objects.select_related('contract').get(id=amendment_id)
    except ContractAmendment.DoesNotExist:
        raise NotFoundError("Amendment not found.")
    
    contract = amendment.contract
    
    # Verify approver is the other party
    if amendment.proposed_by == contract.bid.freelancer:
        expected_approver = contract.bid.project.client
    else:
        expected_approver = contract.bid.freelancer
    
    if approver != expected_approver:
        raise PermissionDeniedError("You cannot approve this amendment.")
    
    # Check status
    if amendment.status != ContractAmendment.Status.PENDING:
        raise ValidationError("Amendment is not pending.")
    
    with transaction.atomic():
        # Update amendment
        amendment.status = ContractAmendment.Status.APPROVED
        amendment.approved_by = approver
        amendment.approved_at = timezone.now()
        amendment.save()
        
        # Apply changes to contract
        if amendment.new_budget:
            contract.agreed_amount = amendment.new_budget
        
        contract.save()
        
        # Update project if needed
        if amendment.new_scope or amendment.new_deadline:
            project = contract.bid.project
            if amendment.new_scope:
                project.description += f"\n\n[Amendment]: {amendment.new_scope}"
            if amendment.new_deadline:
                project.deadline = amendment.new_deadline
            project.save()
        
        # Notify both parties
        from apps.notifications.services import create_notification
        
        create_notification(
            recipient=amendment.proposed_by,
            title="Contract Amendment Approved",
            body="Your amendment request has been approved.",
            type="CONTRACT_AMENDMENT_APPROVED",
            data={"contract_id": contract.id, "amendment_id": amendment.id}
        )
        
        create_notification(
            recipient=approver,
            title="Contract Amendment Applied",
            body="The contract has been updated.",
            type="CONTRACT_AMENDMENT_APPLIED",
            data={"contract_id": contract.id, "amendment_id": amendment.id}
        )
        
        return amendment


def reject_contract_amendment(
    amendment_id: int,
    rejector: User,
    rejection_reason: str,
) -> ContractAmendment:
    """
    Reject a contract amendment.
    
    Args:
        amendment_id: Amendment ID
        rejector: User rejecting the amendment
        rejection_reason: Reason for rejection
    
    Returns:
        Updated ContractAmendment instance
    """
    try:
        amendment = ContractAmendment.objects.select_related('contract').get(id=amendment_id)
    except ContractAmendment.DoesNotExist:
        raise NotFoundError("Amendment not found.")
    
    contract = amendment.contract
    
    # Verify rejector is the other party
    if amendment.proposed_by == contract.bid.freelancer:
        expected_rejector = contract.bid.project.client
    else:
        expected_rejector = contract.bid.freelancer
    
    if rejector != expected_rejector:
        raise PermissionDeniedError("You cannot reject this amendment.")
    
    # Check status
    if amendment.status != ContractAmendment.Status.PENDING:
        raise ValidationError("Amendment is not pending.")
    
    with transaction.atomic():
        amendment.status = ContractAmendment.Status.REJECTED
        amendment.rejection_reason = rejection_reason
        amendment.save()
        
        # Notify proposer
        from apps.notifications.services import create_notification
        create_notification(
            recipient=amendment.proposed_by,
            title="Contract Amendment Rejected",
            body="Your amendment request has been rejected.",
            type="CONTRACT_AMENDMENT_REJECTED",
            data={
                "contract_id": contract.id,
                "amendment_id": amendment.id,
                "rejection_reason": rejection_reason
            }
        )
        
        return amendment


def get_contract_amendments(contract_id: int):
    """Get all amendments for a contract."""
    return ContractAmendment.objects.filter(
        contract_id=contract_id
    ).select_related('proposed_by', 'approved_by').order_by('-created_at')
