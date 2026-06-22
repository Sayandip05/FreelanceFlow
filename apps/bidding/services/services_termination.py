"""Services for Contract Termination."""
from django.db import transaction
from django.utils import timezone

from .models import Contract
from apps.users.models import User
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError


class ContractTerminationReason:
    """Reasons for contract termination."""
    CLIENT_REQUEST = "CLIENT_REQUEST"
    FREELANCER_REQUEST = "FREELANCER_REQUEST"
    MUTUAL_AGREEMENT = "MUTUAL_AGREEMENT"
    BREACH_OF_CONTRACT = "BREACH_OF_CONTRACT"
    NON_PERFORMANCE = "NON_PERFORMANCE"
    SCOPE_CHANGE = "SCOPE_CHANGE"
    OTHER = "OTHER"


def request_contract_termination(
    contract_id: int,
    requester: User,
    reason: str,
    explanation: str,
) -> Contract:
    """
    Request early termination of a contract.
    Requires approval from the other party.
    
    Args:
        contract_id: Contract ID
        requester: User requesting termination
        reason: Termination reason code
        explanation: Detailed explanation
    
    Returns:
        Updated Contract instance
    """
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise NotFoundError("Contract not found.")
    
    # Verify requester is part of contract
    if requester not in [contract.bid.freelancer, contract.bid.project.client]:
        raise PermissionDeniedError("You are not part of this contract.")
    
    # Check contract is active
    if not contract.is_active:
        raise ValidationError("Contract is not active.")
    
    # Check if termination already requested
    if hasattr(contract, 'termination_request'):
        raise ValidationError("Termination request already exists.")
    
    from .models_termination import ContractTerminationRequest
    
    with transaction.atomic():
        termination_request = ContractTerminationRequest.objects.create(
            contract=contract,
            requester=requester,
            reason=reason,
            explanation=explanation,
            status=ContractTerminationRequest.Status.PENDING,
        )
        
        # Notify the other party
        other_party = (
            contract.bid.project.client 
            if requester == contract.bid.freelancer 
            else contract.bid.freelancer
        )
        
        from apps.notifications.services import create_notification
        create_notification(
            recipient=other_party,
            title="Contract Termination Request",
            body=f"{requester.get_full_name()} has requested to terminate the contract.",
            type="CONTRACT_TERMINATION_REQUEST",
            data={
                "contract_id": contract.id,
                "termination_request_id": termination_request.id
            }
        )
        
        return contract


def approve_contract_termination(
    termination_request_id: int,
    approver: User,
    refund_percentage: float = 0,
) -> Contract:
    """
    Approve contract termination request.
    
    Args:
        termination_request_id: Termination request ID
        approver: User approving the termination
        refund_percentage: Percentage of escrow to refund to client (0-100)
    
    Returns:
        Terminated Contract instance
    """
    from .models_termination import ContractTerminationRequest
    
    try:
        termination_request = ContractTerminationRequest.objects.select_related(
            'contract'
        ).get(id=termination_request_id)
    except ContractTerminationRequest.DoesNotExist:
        raise NotFoundError("Termination request not found.")
    
    contract = termination_request.contract
    
    # Verify approver is the other party
    if termination_request.requester == contract.bid.freelancer:
        expected_approver = contract.bid.project.client
    else:
        expected_approver = contract.bid.freelancer
    
    if approver != expected_approver:
        raise PermissionDeniedError("You cannot approve this termination request.")
    
    # Check status
    if termination_request.status != ContractTerminationRequest.Status.PENDING:
        raise ValidationError("Termination request is not pending.")
    
    # Validate refund percentage
    if refund_percentage < 0 or refund_percentage > 100:
        raise ValidationError("Refund percentage must be between 0 and 100.")
    
    with transaction.atomic():
        # Update termination request
        termination_request.status = ContractTerminationRequest.Status.APPROVED
        termination_request.approved_by = approver
        termination_request.approved_at = timezone.now()
        termination_request.refund_percentage = refund_percentage
        termination_request.save()
        
        # Terminate contract
        contract.is_active = False
        contract.end_date = timezone.now()
        contract.termination_reason = termination_request.reason
        contract.save()
        
        # Handle payment/refund if escrow exists
        if hasattr(contract, 'payment'):
            from apps.payments.services import process_contract_termination_payment
            process_contract_termination_payment(
                contract.payment,
                refund_percentage
            )
        
        # Notify both parties
        from apps.notifications.services import create_notification
        
        create_notification(
            recipient=termination_request.requester,
            title="Contract Termination Approved",
            body="Your termination request has been approved.",
            type="CONTRACT_TERMINATED",
            data={"contract_id": contract.id}
        )
        
        create_notification(
            recipient=approver,
            title="Contract Terminated",
            body="The contract has been terminated.",
            type="CONTRACT_TERMINATED",
            data={"contract_id": contract.id}
        )
        
        return contract


def reject_contract_termination(
    termination_request_id: int,
    rejector: User,
    rejection_reason: str,
) -> None:
    """
    Reject contract termination request.
    
    Args:
        termination_request_id: Termination request ID
        rejector: User rejecting the termination
        rejection_reason: Reason for rejection
    """
    from .models_termination import ContractTerminationRequest
    
    try:
        termination_request = ContractTerminationRequest.objects.select_related(
            'contract'
        ).get(id=termination_request_id)
    except ContractTerminationRequest.DoesNotExist:
        raise NotFoundError("Termination request not found.")
    
    contract = termination_request.contract
    
    # Verify rejector is the other party
    if termination_request.requester == contract.bid.freelancer:
        expected_rejector = contract.bid.project.client
    else:
        expected_rejector = contract.bid.freelancer
    
    if rejector != expected_rejector:
        raise PermissionDeniedError("You cannot reject this termination request.")
    
    # Check status
    if termination_request.status != ContractTerminationRequest.Status.PENDING:
        raise ValidationError("Termination request is not pending.")
    
    with transaction.atomic():
        termination_request.status = ContractTerminationRequest.Status.REJECTED
        termination_request.rejection_reason = rejection_reason
        termination_request.save()
        
        # Notify requester
        from apps.notifications.services import create_notification
        create_notification(
            recipient=termination_request.requester,
            title="Contract Termination Rejected",
            body="Your termination request has been rejected.",
            type="CONTRACT_TERMINATION_REJECTED",
            data={
                "contract_id": contract.id,
                "rejection_reason": rejection_reason
            }
        )


def force_terminate_contract(
    contract_id: int,
    admin_user: User,
    reason: str,
    explanation: str,
) -> Contract:
    """
    Force terminate a contract (admin only).
    
    Args:
        contract_id: Contract ID
        admin_user: Admin user
        reason: Termination reason
        explanation: Detailed explanation
    
    Returns:
        Terminated Contract instance
    """
    if not admin_user.is_staff:
        raise PermissionDeniedError("Only admins can force terminate contracts.")
    
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise NotFoundError("Contract not found.")
    
    if not contract.is_active:
        raise ValidationError("Contract is not active.")
    
    with transaction.atomic():
        contract.is_active = False
        contract.end_date = timezone.now()
        contract.termination_reason = reason
        contract.save()
        
        # Notify both parties
        from apps.notifications.services import create_notification
        
        for user in [contract.bid.freelancer, contract.bid.project.client]:
            create_notification(
                recipient=user,
                title="Contract Terminated by Admin",
                body=f"Contract has been terminated. Reason: {explanation}",
                type="CONTRACT_FORCE_TERMINATED",
                data={"contract_id": contract.id}
            )
        
        return contract
