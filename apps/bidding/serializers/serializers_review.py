"""Serializers for Review system."""
from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator

from .models_review import Review, ReviewResponse
from apps.users.serializers import UserSerializer
from core.sanitizers import sanitize_html


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviews."""
    reviewer = UserSerializer(read_only=True)
    reviewee = UserSerializer(read_only=True)
    average_detailed_rating = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id',
            'contract',
            'reviewer',
            'reviewee',
            'reviewer_type',
            'rating',
            'review_text',
            'communication_rating',
            'quality_rating',
            'professionalism_rating',
            'average_detailed_rating',
            'is_public',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['reviewer', 'reviewee', 'reviewer_type', 'created_at', 'updated_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews."""
    
    class Meta:
        model = Review
        fields = [
            'rating',
            'review_text',
            'communication_rating',
            'quality_rating',
            'professionalism_rating',
            'is_public',
        ]
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate_review_text(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Review must be at least 20 characters.")
        # Sanitize to prevent XSS
        return sanitize_html(value, allow_basic_formatting=True)
    
    def validate_communication_rating(self, value):
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate_quality_rating(self, value):
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate_professionalism_rating(self, value):
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ReviewResponseSerializer(serializers.ModelSerializer):
    """Serializer for review responses."""
    
    class Meta:
        model = ReviewResponse
        fields = [
            'id',
            'review',
            'response_text',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ReviewResponseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating review responses."""
    
    class Meta:
        model = ReviewResponse
        fields = ['response_text']
    
    def validate_response_text(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Response must be at least 10 characters.")
        # Sanitize to prevent XSS
        return sanitize_html(value, allow_basic_formatting=True)


class UserRatingsSummarySerializer(serializers.Serializer):
    """Serializer for user ratings summary."""
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    rating_breakdown = serializers.DictField()
    average_communication = serializers.FloatField()
    average_quality = serializers.FloatField()
    average_professionalism = serializers.FloatField()
