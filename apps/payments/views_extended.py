"""
Views for Extended Payment Features
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from .serializers_extended import (
    PaymentMilestoneSerializer, CreateMilestoneSerializer,
    MilestoneProgressSerializer
)
from .services_milestone import (
    create_milestone, complete_milestone, release_milestone_payment,
    get_contract_milestones, get_milestone_progress, get_upcoming_milestones
)


class PaymentMilestoneViewSet(viewsets.ViewSet):
    """
    ViewSet for Payment Milestones
    
    Endpoints:
    - POST /api/payments/contracts/{id}/milestones/ - Create milestone
    - GET /api/payments/contracts/{id}/milestones/ - List milestones
    - POST /api/payments/milestones/{id}/complete/ - Mark complete
    - POST /api/payments/milestones/{id}/release/ - Release payment
    - GET /api/payments/contracts/{id}/milestone-progress/ - Get progress
    - GET /api/payments/milestones/upcoming/ - Get upcoming milestones
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'], url_path='milestones')
    def create_milestone(self, request, pk=None):
        """Create a milestone for a contract"""
        serializer = CreateMilestoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            milestone = create_milestone(
                pk,
                serializer.validated_data['title'],
                serializer.validated_data.get('description', ''),
                serializer.validated_data['amount'],
                serializer.validated_data.get('due_date')
            )
            return Response({
                'message': 'Milestone created successfully',
                'milestone': PaymentMilestoneSerializer(milestone).data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='milestones')
    def list_milestones(self, request, pk=None):
        """Get all milestones for a contract"""
        milestones = get_contract_milestones(pk)
        serializer = PaymentMilestoneSerializer(milestones, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark milestone as completed (by freelancer)"""
        try:
            milestone = complete_milestone(pk, request.user)
            return Response({
                'message': 'Milestone marked as completed',
                'milestone': PaymentMilestoneSerializer(milestone).data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        """Release payment for a completed milestone (by client)"""
        try:
            payment = release_milestone_payment(pk, request.user)
            from .serializers import PaymentSerializer
            return Response({
                'message': 'Milestone payment released',
                'payment': PaymentSerializer(payment).data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='milestone-progress')
    def progress(self, request, pk=None):
        """Get milestone progress for a contract"""
        progress = get_milestone_progress(pk)
        serializer = MilestoneProgressSerializer(data=progress)
        serializer.is_valid()
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming milestones for current user"""
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 10))
        
        milestones = get_upcoming_milestones(request.user, days=days, limit=limit)
        serializer = PaymentMilestoneSerializer(milestones, many=True)
        return Response(serializer.data)
