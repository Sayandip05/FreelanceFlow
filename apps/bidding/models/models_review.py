"""Review and Rating models for completed contracts."""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.users.models import User
from .models import Contract


class Review(models.Model):
    """
    Review and rating for a completed contract.
    Both client and freelancer can leave reviews.
    """
    
    class ReviewerType(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        FREELANCER = "FREELANCER", "Freelancer"
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews_given"
    )
    reviewee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews_received"
    )
    reviewer_type = models.CharField(
        max_length=20,
        choices=ReviewerType.choices
    )
    
    # Rating (1-5 stars)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Review text
    review_text = models.TextField()
    
    # Specific ratings
    communication_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    quality_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    professionalism_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    # Metadata
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "reviews"
        ordering = ["-created_at"]
        unique_together = ["contract", "reviewer"]
        indexes = [
            models.Index(fields=["reviewee", "-created_at"]),
            models.Index(fields=["rating"]),
        ]
    
    def __str__(self):
        return f"Review by {self.reviewer.email} for {self.reviewee.email} - {self.rating}★"
    
    @property
    def average_detailed_rating(self):
        """Calculate average of detailed ratings if provided."""
        ratings = [
            r for r in [
                self.communication_rating,
                self.quality_rating,
                self.professionalism_rating
            ] if r is not None
        ]
        return sum(ratings) / len(ratings) if ratings else self.rating


class ReviewResponse(models.Model):
    """
    Response to a review (optional).
    Allows reviewee to respond to feedback.
    """
    
    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,
        related_name="response"
    )
    response_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "review_responses"
    
    def __str__(self):
        return f"Response to review {self.review.id}"
