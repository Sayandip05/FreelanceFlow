"""Services for Review system."""
from django.db import transaction
from django.db.models import Avg, Count, Q

from .models import Contract
from .models_review import Review, ReviewResponse
from apps.users.models import User
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError


def create_review(
    contract_id: int,
    reviewer: User,
    rating: int,
    review_text: str,
    communication_rating: int = None,
    quality_rating: int = None,
    professionalism_rating: int = None,
    is_public: bool = True,
) -> Review:
    """
    Create a review for a completed contract.
    
    Args:
        contract_id: Contract ID
        reviewer: User leaving the review
        rating: Overall rating (1-5)
        review_text: Review text
        communication_rating: Optional communication rating
        quality_rating: Optional quality rating
        professionalism_rating: Optional professionalism rating
        is_public: Whether review is public
    
    Returns:
        Created Review instance
    """
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise NotFoundError("Contract not found.")
    
    # Verify contract is completed
    if contract.is_active:
        raise ValidationError("Cannot review an active contract.")
    
    # Determine reviewer type and reviewee
    if reviewer == contract.bid.project.client:
        reviewer_type = Review.ReviewerType.CLIENT
        reviewee = contract.bid.freelancer
    elif reviewer == contract.bid.freelancer:
        reviewer_type = Review.ReviewerType.FREELANCER
        reviewee = contract.bid.project.client
    else:
        raise PermissionDeniedError("You are not part of this contract.")
    
    # Check if review already exists
    if Review.objects.filter(contract=contract, reviewer=reviewer).exists():
        raise ValidationError("You have already reviewed this contract.")
    
    with transaction.atomic():
        review = Review.objects.create(
            contract=contract,
            reviewer=reviewer,
            reviewee=reviewee,
            reviewer_type=reviewer_type,
            rating=rating,
            review_text=review_text,
            communication_rating=communication_rating,
            quality_rating=quality_rating,
            professionalism_rating=professionalism_rating,
            is_public=is_public,
        )
        
        # Update user's average rating
        _update_user_rating(reviewee)
        
        # Notify reviewee
        from apps.notifications.services import create_notification
        create_notification(
            recipient=reviewee,
            title="New Review Received",
            body=f"{reviewer.get_full_name()} left you a {rating}-star review.",
            type="REVIEW_RECEIVED",
            data={"review_id": review.id, "contract_id": contract.id}
        )
        
        return review


def update_review(
    review_id: int,
    reviewer: User,
    rating: int = None,
    review_text: str = None,
    communication_rating: int = None,
    quality_rating: int = None,
    professionalism_rating: int = None,
    is_public: bool = None,
) -> Review:
    """Update an existing review."""
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        raise NotFoundError("Review not found.")
    
    if review.reviewer != reviewer:
        raise PermissionDeniedError("You can only update your own reviews.")
    
    if rating is not None:
        review.rating = rating
    if review_text is not None:
        review.review_text = review_text
    if communication_rating is not None:
        review.communication_rating = communication_rating
    if quality_rating is not None:
        review.quality_rating = quality_rating
    if professionalism_rating is not None:
        review.professionalism_rating = professionalism_rating
    if is_public is not None:
        review.is_public = is_public
    
    review.save()
    
    # Update reviewee's average rating
    _update_user_rating(review.reviewee)
    
    return review


def delete_review(review_id: int, reviewer: User) -> None:
    """Delete a review."""
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        raise NotFoundError("Review not found.")
    
    if review.reviewer != reviewer:
        raise PermissionDeniedError("You can only delete your own reviews.")
    
    reviewee = review.reviewee
    review.delete()
    
    # Update reviewee's average rating
    _update_user_rating(reviewee)


def create_review_response(
    review_id: int,
    user: User,
    response_text: str,
) -> ReviewResponse:
    """
    Create a response to a review.
    
    Args:
        review_id: Review ID
        user: User responding (must be reviewee)
        response_text: Response text
    
    Returns:
        Created ReviewResponse instance
    """
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        raise NotFoundError("Review not found.")
    
    if review.reviewee != user:
        raise PermissionDeniedError("Only the reviewee can respond to this review.")
    
    if hasattr(review, 'response'):
        raise ValidationError("Response already exists for this review.")
    
    response = ReviewResponse.objects.create(
        review=review,
        response_text=response_text,
    )
    
    # Notify reviewer
    from apps.notifications.services import create_notification
    create_notification(
        recipient=review.reviewer,
        title="Review Response",
        body=f"{user.get_full_name()} responded to your review.",
        type="REVIEW_RESPONSE",
        data={"review_id": review.id}
    )
    
    return response


def get_user_reviews(user: User, is_public_only: bool = True):
    """Get all reviews received by a user."""
    queryset = Review.objects.filter(reviewee=user).select_related(
        'reviewer', 'contract'
    )
    
    if is_public_only:
        queryset = queryset.filter(is_public=True)
    
    return queryset


def get_user_rating_summary(user: User) -> dict:
    """
    Get rating summary for a user.
    
    Returns:
        Dict with average rating, total reviews, and breakdown
    """
    reviews = Review.objects.filter(reviewee=user, is_public=True)
    
    if not reviews.exists():
        return {
            'average_rating': 0,
            'total_reviews': 0,
            'rating_breakdown': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'average_communication': 0,
            'average_quality': 0,
            'average_professionalism': 0,
        }
    
    # Calculate averages
    aggregates = reviews.aggregate(
        avg_rating=Avg('rating'),
        avg_communication=Avg('communication_rating'),
        avg_quality=Avg('quality_rating'),
        avg_professionalism=Avg('professionalism_rating'),
        total=Count('id'),
    )
    
    # Rating breakdown
    rating_breakdown = {}
    for i in range(1, 6):
        rating_breakdown[i] = reviews.filter(rating=i).count()
    
    return {
        'average_rating': round(aggregates['avg_rating'], 2),
        'total_reviews': aggregates['total'],
        'rating_breakdown': rating_breakdown,
        'average_communication': round(aggregates['avg_communication'] or 0, 2),
        'average_quality': round(aggregates['avg_quality'] or 0, 2),
        'average_professionalism': round(aggregates['avg_professionalism'] or 0, 2),
    }


def _update_user_rating(user: User) -> None:
    """Update user's cached average rating."""
    summary = get_user_rating_summary(user)
    
    if user.role == User.Roles.FREELANCER:
        profile = user.freelancer_profile
        profile.average_rating = summary['average_rating']
        profile.total_reviews = summary['total_reviews']
        profile.save()
    elif user.role == User.Roles.CLIENT:
        profile = user.client_profile
        profile.average_rating = summary['average_rating']
        profile.total_reviews = summary['total_reviews']
        profile.save()
