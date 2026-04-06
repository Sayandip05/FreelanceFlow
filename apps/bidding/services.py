from django.db import transaction
from django.utils import timezone

from .models import Bid, Contract
from apps.projects.models import Project
from apps.projects.services import mark_project_in_progress
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError


def submit_bid(
    freelancer,
    project_id: int,
    amount: float,
    cover_letter: str,
) -> Bid:
    """
    Submit a bid on a project.
    
    Args:
        freelancer: User instance (must be freelancer)
        project_id: Project ID
        amount: Bid amount
        cover_letter: Proposal text
    
    Returns:
        Created Bid instance
    """
    from apps.users.models import User
    
    if freelancer.role != User.Roles.FREELANCER:
        raise PermissionDeniedError("Only freelancers can submit bids.")
    
    # Get project
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        raise NotFoundError("Project not found.")
    
    # Validate project is open
    if project.status != Project.Status.OPEN:
        raise ValidationError("Project is not open for bidding.")
    
    # Check freelancer hasn't already bid
    if Bid.objects.filter(freelancer=freelancer, project=project).exists():
        raise ValidationError(
            "You have already submitted a bid on this project.",
            field="project"
        )
    
    # Validate amount
    if amount <= 0:
        raise ValidationError("Bid amount must be greater than 0.", field="amount")
    
    if amount > project.budget:
        raise ValidationError(
            "Bid amount cannot exceed project budget.",
            field="amount"
        )
    
    # Validate cover letter
    if not cover_letter or len(cover_letter.strip()) < 50:
        raise ValidationError(
            "Cover letter must be at least 50 characters.",
            field="cover_letter"
        )
    
    with transaction.atomic():
        bid = Bid.objects.create(
            project=project,
            freelancer=freelancer,
            amount=amount,
            cover_letter=cover_letter,
            status=Bid.Status.PENDING,
        )
        
        return bid


def accept_bid(bid_id: int, client) -> Contract:
    """
    Accept a bid and create a contract.
    Uses select_for_update to prevent race conditions.
    
    Args:
        bid_id: Bid ID
        client: User instance (must be project owner)
    
    Returns:
        Created Contract instance
    """
    from apps.notifications.services import create_notification
    from apps.notifications.tasks import notify_freelancer_bid_accepted
    
    with transaction.atomic():
        # Lock the bid row to prevent concurrent modifications
        try:
            bid = Bid.objects.select_for_update().get(id=bid_id)
        except Bid.DoesNotExist:
            raise NotFoundError("Bid not found.")
        
        # Verify client owns the project
        if bid.project.client != client:
            raise PermissionDeniedError(
                "Only the project owner can accept bids."
            )
        
        # Verify project is still open
        if bid.project.status != Project.Status.OPEN:
            raise ValidationError("Project is no longer open.")
        
        # Verify bid is pending
        if bid.status != Bid.Status.PENDING:
            raise ValidationError("Bid is no longer pending.")
        
        # Update bid status
        bid.status = Bid.Status.ACCEPTED
        bid.save()
        
        # Reject all other bids on this project
        Bid.objects.filter(
            project=bid.project
        ).exclude(id=bid.id).update(status=Bid.Status.REJECTED)
        
        # Create contract
        contract = Contract.objects.create(
            bid=bid,
            agreed_amount=bid.amount,
        )
        
        # Update project status
        mark_project_in_progress(bid.project)
        
        # Schedule notification after commit
        transaction.on_commit(
            lambda: notify_freelancer_bid_accepted.delay(contract.id)
        )
        
        return contract


def reject_bid(bid_id: int, client) -> Bid:
    """
    Reject a bid.
    
    Args:
        bid_id: Bid ID
        client: User instance (must be project owner)
    
    Returns:
        Updated Bid instance
    """
    try:
        bid = Bid.objects.get(id=bid_id)
    except Bid.DoesNotExist:
        raise NotFoundError("Bid not found.")
    
    # Verify client owns the project
    if bid.project.client != client:
        raise PermissionDeniedError(
            "Only the project owner can reject bids."
        )
    
    # Verify bid is pending
    if bid.status != Bid.Status.PENDING:
        raise ValidationError("Bid is no longer pending.")
    
    bid.status = Bid.Status.REJECTED
    bid.save()
    
    return bid


def withdraw_bid(bid_id: int, freelancer) -> Bid:
    """
    Withdraw a bid (freelancer cancels their bid).
    
    Args:
        bid_id: Bid ID
        freelancer: User instance (must be bid owner)
    
    Returns:
        Updated Bid instance
    """
    try:
        bid = Bid.objects.get(id=bid_id)
    except Bid.DoesNotExist:
        raise NotFoundError("Bid not found.")
    
    # Verify freelancer owns the bid
    if bid.freelancer != freelancer:
        raise PermissionDeniedError("You can only withdraw your own bids.")
    
    # Verify bid is still pending
    if bid.status != Bid.Status.PENDING:
        raise ValidationError("Cannot withdraw a bid that is not pending.")
    
    bid.status = Bid.Status.WITHDRAWN
    bid.save()
    
    return bid


def complete_contract(contract_id: int) -> Contract:
    """
    Mark a contract as completed.
    Called when payment is released.
    
    Args:
        contract_id: Contract ID
    
    Returns:
        Updated Contract instance
    """
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise NotFoundError("Contract not found.")
    
    contract.is_active = False
    contract.end_date = timezone.now()
    contract.save()
    
    return contract
