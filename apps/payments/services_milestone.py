"""
Payment Milestone Services
Manages milestone-based payments for contracts
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models_extended import PaymentMilestone
from .models import Payment
from apps/bidding.models import Contract


@transaction.atomic
def create_milestone(contract_id, title, description, amount, due_date=None):
    """
    Create a payment milestone for a contract
    
    Args:
        contract_id: ID of the contract
        title: Milestone title
        description: Milestone description
        amount: Payment amount for this milestone
        due_date: Optional due date
    
    Returns:
        PaymentMilestone instance
    """
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise ValidationError("Contract not found")
    
    # Validate amount
    if amount <= 0:
        raise ValidationError("Amount must be positive")
    
    # Check total milestones don't exceed contract amount
    total_milestones = PaymentMilestone.objects.filter(
        contract=contract
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    
    if total_milestones + amount > contract.agreed_amount:
        raise ValidationError(
            f"Total milestones ({total_milestones + amount}) "
            f"exceed contract amount ({contract.agreed_amount})"
        )
    
    milestone = PaymentMilestone.objects.create(
        contract=contract,
        title=title,
        description=description,
        amount=amount,
        due_date=due_date,
        status=PaymentMilestone.Status.PENDING
    )
    
    return milestone


@transaction.atomic
def complete_milestone(milestone_id, user):
    """
    Mark milestone as completed (by freelancer)
    
    Args:
        milestone_id: ID of the milestone
        user: User instance (must be freelancer)
    
    Returns:
        PaymentMilestone instance
    """
    try:
        milestone = PaymentMilestone.objects.select_related('contract').get(id=milestone_id)
    except PaymentMilestone.DoesNotExist:
        raise ValidationError("Milestone not found")
    
    # Verify user is freelancer
    if milestone.contract.bid.freelancer != user:
        raise ValidationError("Only freelancer can mark milestone as completed")
    
    # Check status
    if milestone.status != PaymentMilestone.Status.PENDING:
        raise ValidationError(f"Milestone status is {milestone.status}")
    
    milestone.status = PaymentMilestone.Status.COMPLETED
    milestone.completed_at = timezone.now()
    milestone.save()
    
    return milestone


@transaction.atomic
def release_milestone_payment(milestone_id, client):
    """
    Release payment for a completed milestone
    
    Args:
        milestone_id: ID of the milestone
        client: User instance (must be project owner)
    
    Returns:
        Payment instance
    """
    from .services import release_payment
    
    try:
        milestone = PaymentMilestone.objects.select_related(
            'contract', 'contract__bid', 'contract__bid__project'
        ).get(id=milestone_id)
    except PaymentMilestone.DoesNotExist:
        raise ValidationError("Milestone not found")
    
    # Verify user is client
    if milestone.contract.bid.project.client != client:
        raise ValidationError("Only project owner can release milestone payments")
    
    # Check milestone status
    if milestone.status != PaymentMilestone.Status.COMPLETED:
        raise ValidationError("Milestone must be completed before payment release")
    
    # Check if already paid
    if milestone.payment_id:
        raise ValidationError("Milestone already paid")
    
    # Create payment for milestone
    payment = Payment.objects.create(
        contract=milestone.contract,
        total_amount=milestone.amount,
        status=Payment.Status.PENDING
    )
    
    # Link payment to milestone
    milestone.payment = payment
    milestone.status = PaymentMilestone.Status.PAID
    milestone.save()
    
    # Release payment
    release_payment(payment.id)
    
    return payment


def get_contract_milestones(contract_id):
    """Get all milestones for a contract"""
    return PaymentMilestone.objects.filter(
        contract_id=contract_id
    ).order_by('due_date', 'created_at')


def get_milestone_progress(contract_id):
    """
    Get milestone progress for a contract
    
    Returns:
        Dict with total/completed/paid amounts and counts
    """
    from django.db.models import Sum, Count, Q
    
    stats = PaymentMilestone.objects.filter(
        contract_id=contract_id
    ).aggregate(
        total_amount=Sum('amount'),
        total_count=Count('id'),
        completed_count=Count('id', filter=Q(status=PaymentMilestone.Status.COMPLETED)),
        paid_count=Count('id', filter=Q(status=PaymentMilestone.Status.PAID)),
        paid_amount=Sum('amount', filter=Q(status=PaymentMilestone.Status.PAID))
    )
    
    return stats


def get_upcoming_milestones(user, days=30, limit=10):
    """Get upcoming milestones for a user (client or freelancer)"""
    from datetime import timedelta
    from django.utils import timezone
    
    end_date = timezone.now().date() + timedelta(days=days)
    
    # Get contracts where user is involved
    from apps.bidding.models import Bid
    
    if user.role == 'CLIENT':
        contract_ids = Contract.objects.filter(
            bid__project__client=user
        ).values_list('id', flat=True)
    else:
        contract_ids = Contract.objects.filter(
            bid__freelancer=user
        ).values_list('id', flat=True)
    
    return PaymentMilestone.objects.filter(
        contract_id__in=contract_ids,
        status=PaymentMilestone.Status.PENDING,
        due_date__lte=end_date
    ).select_related('contract').order_by('due_date')[:limit]
