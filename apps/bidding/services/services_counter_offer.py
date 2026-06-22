"""
Counter-Offer Services
Allows clients to make counter-offers on bids
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Bid
from .models_extended import CounterOffer


@transaction.atomic
def create_counter_offer(bid_id, client, counter_amount, counter_timeline=None, message=None):
    """
    Create a counter-offer on a bid
    
    Args:
        bid_id: ID of the bid
        client: User instance (must be project owner)
        counter_amount: Counter-offered amount
        counter_timeline: Counter-offered timeline in days
        message: Optional message to freelancer
    
    Returns:
        CounterOffer instance
    
    Raises:
        ValidationError: If counter-offer cannot be created
    """
    try:
        bid = Bid.objects.select_related('project').get(id=bid_id)
    except Bid.DoesNotExist:
        raise ValidationError("Bid not found")
    
    # Verify client is project owner
    if bid.project.client != client:
        raise ValidationError("Only project owner can make counter-offers")
    
    # Check bid status
    if bid.status != Bid.Status.PENDING:
        raise ValidationError(f"Cannot counter-offer on bid with status: {bid.status}")
    
    # Validate amount
    if counter_amount <= 0:
        raise ValidationError("Counter amount must be positive")
    
    # Create counter-offer
    counter_offer = CounterOffer.objects.create(
        bid=bid,
        offered_by=client,
        counter_amount=counter_amount,
        counter_timeline=counter_timeline,
        message=message,
        status=CounterOffer.Status.PENDING
    )
    
    return counter_offer


@transaction.atomic
def accept_counter_offer(counter_offer_id, freelancer):
    """
    Accept a counter-offer
    
    Args:
        counter_offer_id: ID of the counter-offer
        freelancer: User instance (must be bid owner)
    
    Returns:
        Updated Bid instance
    
    Raises:
        ValidationError: If counter-offer cannot be accepted
    """
    try:
        counter_offer = CounterOffer.objects.select_related('bid').get(id=counter_offer_id)
    except CounterOffer.DoesNotExist:
        raise ValidationError("Counter-offer not found")
    
    # Verify freelancer is bid owner
    if counter_offer.bid.freelancer != freelancer:
        raise ValidationError("Only bid owner can accept counter-offers")
    
    # Check counter-offer status
    if counter_offer.status != CounterOffer.Status.PENDING:
        raise ValidationError(f"Counter-offer status is {counter_offer.status}")
    
    # Update counter-offer
    counter_offer.status = CounterOffer.Status.ACCEPTED
    counter_offer.responded_at = timezone.now()
    counter_offer.save()
    
    # Update bid with counter-offered amount
    bid = counter_offer.bid
    bid.amount = counter_offer.counter_amount
    bid.save()
    
    return bid


@transaction.atomic
def reject_counter_offer(counter_offer_id, freelancer, reason=None):
    """
    Reject a counter-offer
    
    Args:
        counter_offer_id: ID of the counter-offer
        freelancer: User instance (must be bid owner)
        reason: Optional rejection reason
    
    Returns:
        CounterOffer instance
    
    Raises:
        ValidationError: If counter-offer cannot be rejected
    """
    try:
        counter_offer = CounterOffer.objects.get(id=counter_offer_id)
    except CounterOffer.DoesNotExist:
        raise ValidationError("Counter-offer not found")
    
    # Verify freelancer is bid owner
    if counter_offer.bid.freelancer != freelancer:
        raise ValidationError("Only bid owner can reject counter-offers")
    
    # Check counter-offer status
    if counter_offer.status != CounterOffer.Status.PENDING:
        raise ValidationError(f"Counter-offer status is {counter_offer.status}")
    
    # Update counter-offer
    counter_offer.status = CounterOffer.Status.REJECTED
    counter_offer.responded_at = timezone.now()
    if reason:
        counter_offer.message = f"{counter_offer.message}\n\nRejection reason: {reason}"
    counter_offer.save()
    
    return counter_offer


def get_counter_offers_for_bid(bid_id):
    """Get all counter-offers for a bid"""
    return CounterOffer.objects.filter(
        bid_id=bid_id
    ).order_by('-created_at')


def get_pending_counter_offers(freelancer, limit=20):
    """Get pending counter-offers for a freelancer"""
    return CounterOffer.objects.filter(
        bid__freelancer=freelancer,
        status=CounterOffer.Status.PENDING
    ).select_related('bid', 'bid__project', 'offered_by').order_by('-created_at')[:limit]


def get_counter_offer_stats(user):
    """
    Get counter-offer statistics for a user
    
    Returns:
        Dict with sent/received/accepted/rejected counts
    """
    from django.db.models import Count, Q
    
    # For clients (sent counter-offers)
    sent_stats = CounterOffer.objects.filter(
        offered_by=user
    ).aggregate(
        total_sent=Count('id'),
        accepted=Count('id', filter=Q(status=CounterOffer.Status.ACCEPTED)),
        rejected=Count('id', filter=Q(status=CounterOffer.Status.REJECTED)),
        pending=Count('id', filter=Q(status=CounterOffer.Status.PENDING))
    )
    
    # For freelancers (received counter-offers)
    received_stats = CounterOffer.objects.filter(
        bid__freelancer=user
    ).aggregate(
        total_received=Count('id'),
        accepted=Count('id', filter=Q(status=CounterOffer.Status.ACCEPTED)),
        rejected=Count('id', filter=Q(status=CounterOffer.Status.REJECTED)),
        pending=Count('id', filter=Q(status=CounterOffer.Status.PENDING))
    )
    
    return {
        'sent': sent_stats,
        'received': received_stats
    }
