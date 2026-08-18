import logging
import datetime
import calendar
from decimal import Decimal, ROUND_DOWN
from django.db import transaction
from django.utils import timezone
from apps.bidding.models import Bid, Contract
from apps.projects.models import Project
from apps.projects.services import mark_project_in_progress
from apps.payments.models.models_milestone import PaymentMilestone
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError
logger = logging.getLogger("apps.bidding")


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

        from apps.notifications.services import notify_bid_submitted
        transaction.on_commit(
            lambda: notify_bid_submitted(
                project_owner=project.client,
                project_title=project.title,
                freelancer_name=freelancer.get_full_name(),
            )
        )

    logger.info(
        "Bid submitted: bid_id=%s project_id=%s freelancer_id=%s amount=%s",
        bid.id, project.id, freelancer.id, amount,
    )
    return bid


def _get_due_date(start_date, i, frequency):
    if frequency == 'weekly':
        return start_date + datetime.timedelta(weeks=i)
    elif frequency == 'monthly':
        month = start_date.month - 1 + i
        year = start_date.year + month // 12
        month = month % 12 + 1
        day = min(start_date.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)
    return start_date + datetime.timedelta(days=i)


def accept_bid(
    bid_id: int, 
    client, 
    milestones_mode: str = "auto",
    milestone_count: int = 1,
    frequency: str = "monthly",
    start_date = None,
    custom_milestones: list = None
) -> Contract:
    """
    Accept a bid and propose a contract with milestones.
    Uses select_for_update to prevent race conditions.
    """
    from apps.notifications.tasks import notify_freelancer_bid_accepted

    if milestones_mode not in ["auto", "manual"]:
        raise ValidationError("milestones_mode must be 'auto' or 'manual'.")

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
        
        # Prepare milestones to create
        milestones_to_create = []
        bid_amount = Decimal(str(bid.amount))
        
        if milestones_mode == "auto":
            if milestone_count < 1:
                raise ValidationError("milestone_count must be at least 1.")
            
            # Parse start date or use today
            if start_date:
                if isinstance(start_date, str):
                    parsed_start = datetime.datetime.strptime(start_date.split('T')[0], "%Y-%m-%d").date()
                else:
                    parsed_start = start_date
            else:
                parsed_start = timezone.now().date()

            # Split budget equally, with last milestone absorbing the remainder
            base_amount = (bid_amount / milestone_count).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            last_amount = bid_amount - (base_amount * (milestone_count - 1))
            
            for i in range(1, milestone_count + 1):
                amount = last_amount if i == milestone_count else base_amount
                due_date = _get_due_date(parsed_start, i, frequency)
                milestones_to_create.append({
                    "title": f"Milestone {i}",
                    "description": f"Automatically generated Milestone {i} for '{bid.project.title}'",
                    "amount": amount,
                    "percentage": (amount / bid_amount) * Decimal('100'),
                    "order": i,
                    "due_date": due_date,
                    "status": PaymentMilestone.Status.PENDING
                })
        else:
            if not custom_milestones or not isinstance(custom_milestones, list):
                raise ValidationError("custom_milestones list must be provided in manual mode.")
            
            total_sum = Decimal('0.00')
            for i, ms in enumerate(custom_milestones, 1):
                title = ms.get("title")
                desc = ms.get("description", "")
                amount_val = ms.get("amount")
                due_date_str = ms.get("due_date")
                
                if not title:
                    raise ValidationError(f"Milestone {i} is missing a title.")
                if amount_val is None:
                    raise ValidationError(f"Milestone {i} is missing an amount.")
                
                amount = Decimal(str(amount_val))
                if amount <= 0:
                    raise ValidationError(f"Milestone {i} amount must be positive.")
                
                total_sum += amount
                
                due_date = None
                if due_date_str:
                    due_date = datetime.datetime.strptime(due_date_str.split('T')[0], "%Y-%m-%d").date()
                
                milestones_to_create.append({
                    "title": title,
                    "description": desc,
                    "amount": amount,
                    "percentage": (amount / bid_amount) * Decimal('100'),
                    "order": i,
                    "due_date": due_date,
                    "status": PaymentMilestone.Status.PENDING
                })
            
            if total_sum != bid_amount:
                raise ValidationError(f"Total milestone amounts ({total_sum}) must sum exactly to the bid amount ({bid_amount}).")

        # Update bid status
        bid.status = Bid.Status.ACCEPTED
        bid.save()
        
        # Reject all other bids on this project
        Bid.objects.filter(
            project=bid.project
        ).exclude(id=bid.id).update(status=Bid.Status.REJECTED)
        
        # Create contract (will be in PENDING_ACCEPTANCE by default)
        contract = Contract.objects.create(
            bid=bid,
            agreed_amount=bid.amount,
            status=Contract.Status.PENDING_ACCEPTANCE
        )
        
        # Create milestones
        for ms_data in milestones_to_create:
            PaymentMilestone.objects.create(
                contract=contract,
                **ms_data
            )
        
        # Schedule notification after commit
        transaction.on_commit(
            lambda: notify_freelancer_bid_accepted.delay(contract.id)
        )

        logger.info(
            "Bid accepted: bid_id=%s contract_id=%s project_id=%s client_id=%s freelancer_id=%s",
            bid.id, contract.id, bid.project.id, client.id, bid.freelancer.id,
        )
        return contract


def accept_contract(contract_id: int, freelancer) -> Contract:
    """
    Accept a contract proposal (freelancer only).
    Marks contract as ACTIVE and project as IN_PROGRESS.
    """
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise NotFoundError("Contract not found.")

    if contract.bid.freelancer != freelancer:
        raise PermissionDeniedError("Only the freelancer can accept this contract.")

    if contract.status != Contract.Status.PENDING_ACCEPTANCE:
        raise ValidationError("Contract is not pending acceptance.")

    with transaction.atomic():
        contract.status = Contract.Status.ACTIVE
        contract.save()
        
        # Mark project as IN_PROGRESS
        mark_project_in_progress(contract.bid.project)
        
        # Create notification for client
        from apps.notifications.services import create_notification
        create_notification(
            recipient=contract.bid.project.client,
            title="Contract Accepted!",
            body=f"{freelancer.get_full_name()} has accepted the contract for '{contract.bid.project.title}'. Work can now begin.",
            type="CONTRACT_ACCEPTED",
            data={"contract_id": contract.id}
        )

    logger.info("Contract accepted: contract_id=%s freelancer_id=%s", contract.id, freelancer.id)
    return contract


def decline_contract(contract_id: int, freelancer) -> None:
    """
    Decline a contract proposal (freelancer only).
    Deletes the contract, reverts the freelancer's bid to PENDING,
    and reverts other REJECTED bids on that project back to PENDING.
    """
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise NotFoundError("Contract not found.")

    if contract.bid.freelancer != freelancer:
        raise PermissionDeniedError("Only the freelancer can decline this contract.")

    if contract.status != Contract.Status.PENDING_ACCEPTANCE:
        raise ValidationError("Contract is not pending acceptance.")

    project = contract.bid.project
    bid = contract.bid

    with transaction.atomic():
        # Revert bid status to PENDING
        bid.status = Bid.Status.PENDING
        bid.save()

        # Revert other rejected bids to PENDING
        Bid.objects.filter(project=project, status=Bid.Status.REJECTED).update(status=Bid.Status.PENDING)

        # Delete contract (will cascade delete milestones)
        contract.delete()

        # Create notification for client
        from apps.notifications.services import create_notification
        create_notification(
            recipient=project.client,
            title="Contract Proposal Declined",
            body=f"{freelancer.get_full_name()} has declined the contract proposal for '{project.title}'. You can now select another freelancer.",
            type="CONTRACT_DECLINED",
            data={"project_id": project.id}
        )

    logger.info("Contract declined and deleted: contract_id=%s freelancer_id=%s", contract_id, freelancer.id)


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

    logger.info(
        "Bid rejected: bid_id=%s project_id=%s client_id=%s",
        bid.id, bid.project.id, client.id,
    )
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

    logger.info(
        "Bid withdrawn: bid_id=%s project_id=%s freelancer_id=%s",
        bid.id, bid.project.id, freelancer.id,
    )
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

    logger.info(
        "Contract completed: contract_id=%s project_id=%s",
        contract.id, contract.bid.project.id,
    )
    return contract
