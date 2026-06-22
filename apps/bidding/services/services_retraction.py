"""
Bid Retraction Services
Allows freelancers to retract bids before acceptance
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Bid
from .models_extended import BidRetraction


@transaction.atomic
def retract_bid(bid_id, freelancer, reason):
    """
    Retract a bid
    
    Args:
        bid_id: ID of the bid to retract
        freelancer: User instance (must be the bid owner)
        reason: Reason for retraction
    
    Returns:
        BidRetraction instance
    
    Raises:
        ValidationError: If bid cannot be retracted
    """
    try:
        bid = Bid.objects.select_for_update().get(id=bid_id)
    except Bid.DoesNotExist:
        raise ValidationError("Bid not found")
    
    # Verify ownership
    if bid.freelancer != freelancer:
        raise ValidationError("You can only retract your own bids")
    
    # Check if bid is still pending
    if bid.status != Bid.Status.PENDING:
        raise ValidationError(f"Cannot retract bid with status: {bid.status}")
    
    # Check if already retracted
    if BidRetraction.objects.filter(bid=bid).exists():
        raise ValidationError("Bid already retracted")
    
    # Create retraction record
    retraction = BidRetraction.objects.create(
        bid=bid,
        reason=reason
    )
    
    # Update bid status
    bid.status = Bid.Status.RETRACTED
    bid.save()
    
    return retraction


def can_retract_bid(bid, user):
    """
    Check if a bid can be retracted
    
    Returns:
        (can_retract: bool, reason: str)
    """
    # Must be bid owner
    if bid.freelancer != user:
        return False, "Not bid owner"
    
    # Must be pending
    if bid.status != Bid.Status.PENDING:
        return False, f"Bid status is {bid.status}"
    
    # Must not be already retracted
    if BidRetraction.objects.filter(bid=bid).exists():
        return False, "Already retracted"
    
    return True, "Can retract"


def get_retracted_bids(freelancer, limit=20):
    """Get all retracted bids for a freelancer"""
    retraction_ids = BidRetraction.objects.filter(
        bid__freelancer=freelancer
    ).values_list('bid_id', flat=True)
    
    return Bid.objects.filter(
        id__in=retraction_ids
    ).select_related('project', 'freelancer').order_by('-created_at')[:limit]


def get_retraction_details(bid_id):
    """Get retraction details for a bid"""
    try:
        retraction = BidRetraction.objects.select_related('bid').get(bid_id=bid_id)
        return {
            'bid_id': retraction.bid_id,
            'reason': retraction.reason,
            'retracted_at': retraction.retracted_at,
            'bid_amount': retraction.bid.amount,
            'project_title': retraction.bid.project.title
        }
    except BidRetraction.DoesNotExist:
        return None
