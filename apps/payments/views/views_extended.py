"""
Views for Extended Payment Features
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from apps.payments.serializers.serializers_extended import (
    PaymentMilestoneSerializer, CreateMilestoneSerializer,
    MilestoneProgressSerializer
)
from apps.payments.services.services_milestone import (
    create_milestone, complete_milestone, release_milestone_payment,
    get_contract_milestones, get_milestone_progress, get_upcoming_milestones
)


class PaymentMilestoneViewSet(viewsets.ViewSet):
    """
    ViewSet for Payment Milestones
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """List all milestones for the authenticated user."""
        from apps.payments.models import PaymentMilestone
        user = request.user
        if getattr(user, 'role', None) == 'CLIENT':
            milestones = PaymentMilestone.objects.filter(contract__bid__project__client=user)
        else:
            milestones = PaymentMilestone.objects.filter(contract__bid__freelancer=user)
        serializer = PaymentMilestoneSerializer(milestones, many=True)
        return Response(serializer.data)


    
    @action(detail=True, methods=['post'], url_path='clear')
    def clear_milestones(self, request, pk=None):
        """Delete all milestones for a contract (only allowed if pending acceptance, or active without any funded/submitted milestones)"""
        from apps.bidding.models import Contract
        try:
            contract = Contract.objects.get(id=pk)
            has_activity = contract.milestones.exclude(status='PENDING').exists()
            if contract.status not in [Contract.Status.PENDING_ACCEPTANCE, Contract.Status.ACTIVE] or has_activity:
                return Response({'error': 'Cannot modify milestones once funding has started or contract is closed.'}, status=status.HTTP_400_BAD_REQUEST)
            contract.milestones.all().delete()
            return Response({'message': 'All milestones cleared successfully.'})
        except Contract.DoesNotExist:
            return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get', 'post'], url_path='milestones')
    def manage_milestones(self, request, pk=None):
        """Get or create milestones for a contract"""
        if request.method == 'GET':
            milestones = get_contract_milestones(pk)
            serializer = PaymentMilestoneSerializer(milestones, many=True)
            return Response(serializer.data)
            
        elif request.method == 'POST':
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
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark milestone as completed (by freelancer)"""
        desc = request.data.get("deliverable_description", "")
        files = request.data.get("deliverable_files", [])
        try:
            milestone = complete_milestone(
                pk, 
                request.user, 
                deliverable_description=desc, 
                deliverable_files=files
            )
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
    def fund(self, request, pk=None):
        """Fund escrow for a specific milestone (by client)"""
        from apps.payments.models.models_milestone import PaymentMilestone
        from apps.payments.services import create_milestone_escrow
        from apps.payments.serializers import PaymentSerializer
        try:
            milestone = PaymentMilestone.objects.select_related('contract', 'contract__bid__project').get(id=pk)
            payment = create_milestone_escrow(milestone.contract, request.user, milestone)
            return Response({
                'message': 'Escrow order created successfully',
                'payment': PaymentSerializer(payment).data
            }, status=status.HTTP_201_CREATED)
        except PaymentMilestone.DoesNotExist:
            return Response({'error': 'Milestone not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        """Release payment for a completed milestone (by client)"""
        try:
            payment = release_milestone_payment(pk, request.user)
            from apps.payments.serializers import PaymentSerializer
            return Response({
                'message': 'Milestone payment release initiated',
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
