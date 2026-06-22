"""Views for Review system."""
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models

from .models_review import Review, ReviewResponse
from .serializers_review import (
    ReviewSerializer,
    ReviewCreateSerializer,
    ReviewResponseSerializer,
    ReviewResponseCreateSerializer,
    UserRatingsSummarySerializer,
)
from .services_review import (
    create_review,
    update_review,
    delete_review,
    create_review_response,
    get_user_reviews,
    get_user_rating_summary,
)
from core.exceptions import ValidationError
from core.pagination import StandardResultsPagination


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Review operations.
    
    Endpoints:
    - GET /api/reviews/ - List user's reviews
    - POST /api/reviews/ - Create review for completed contract
    - GET /api/reviews/{id}/ - Get review detail
    - PATCH /api/reviews/{id}/ - Update review
    - DELETE /api/reviews/{id}/ - Delete review
    - POST /api/reviews/{id}/respond/ - Respond to review
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsPagination
    
    def get_queryset(self):
        user = self.request.user
        
        # Show reviews given by user or received by user
        return Review.objects.filter(
            models.Q(reviewer=user) | models.Q(reviewee=user)
        ).select_related('reviewer', 'reviewee', 'contract')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a review for a completed contract."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contract_id = request.data.get('contract_id')
        if not contract_id:
            return Response(
                {"error": "Contract ID required.", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            review = create_review(
                contract_id=int(contract_id),
                reviewer=request.user,
                rating=serializer.validated_data['rating'],
                review_text=serializer.validated_data['review_text'],
                communication_rating=serializer.validated_data.get('communication_rating'),
                quality_rating=serializer.validated_data.get('quality_rating'),
                professionalism_rating=serializer.validated_data.get('professionalism_rating'),
                is_public=serializer.validated_data.get('is_public', True),
            )
            
            return Response(
                ReviewSerializer(review).data,
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    def update(self, request, *args, **kwargs):
        """Update a review."""
        partial = kwargs.pop('partial', False)
        review = self.get_object()
        serializer = ReviewCreateSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_review = update_review(
                review_id=review.id,
                reviewer=request.user,
                rating=serializer.validated_data.get('rating'),
                review_text=serializer.validated_data.get('review_text'),
                communication_rating=serializer.validated_data.get('communication_rating'),
                quality_rating=serializer.validated_data.get('quality_rating'),
                professionalism_rating=serializer.validated_data.get('professionalism_rating'),
                is_public=serializer.validated_data.get('is_public'),
            )
            
            return Response(
                ReviewSerializer(updated_review).data,
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a review."""
        review = self.get_object()
        
        try:
            delete_review(review.id, request.user)
            return Response(
                {"message": "Review deleted successfully."},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to a review (reviewee only)."""
        review = self.get_object()
        serializer = ReviewResponseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            response = create_review_response(
                review_id=review.id,
                user=request.user,
                response_text=serializer.validated_data['response_text'],
            )
            
            return Response(
                ReviewResponseSerializer(response).data,
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=False, methods=['get'])
    def received(self, request):
        """Get reviews received by current user."""
        reviews = get_user_reviews(request.user, is_public_only=False)
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def given(self, request):
        """Get reviews given by current user."""
        reviews = Review.objects.filter(reviewer=request.user).select_related(
            'reviewee', 'contract'
        )
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def user_reviews(self, request, user_id=None):
        """Get public reviews for a specific user."""
        from apps.users.models import User
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found.", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        reviews = get_user_reviews(user, is_public_only=True)
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)/summary')
    def user_rating_summary(self, request, user_id=None):
        """Get rating summary for a specific user."""
        from apps.users.models import User
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found.", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        summary = get_user_rating_summary(user)
        serializer = UserRatingsSummarySerializer(summary)
        return Response(serializer.data)
