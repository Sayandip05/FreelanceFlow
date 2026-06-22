"""
Views for Extended Bidding Features
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from .serializers_extended import (
    WorklogApprovalSerializer, ApproveWorklogSerializer, RejectWorklogSerializer,
    BidRetractionSerializer, RetractionDetailSerializer,
    CounterOfferSerializer, CounterOfferResponseSerializer,
    CounterOfferStatsSerializer
)
from .services_worklog_approval import (
    submit_worklog_for_approval, approve_worklog, reject_worklog,
    get_pending_approvals, get_worklog_approval_status, get_approval_stats
)
from .services_retraction import (
    retract_bid, can_retract_bid, get_retracted_bids, get_retraction_details
)
from .services_counter_offer import (
    create_counter_offer, accept_counter_offer, reject_counter_offer,
    get_counter_offers_for_bid, get_pending_counter_offers, get_counter_offer_stats
)


class WorklogApprovalViewSet(viewsets.ViewSet):
    """
    ViewSet for Worklog Approval
    
    Endpoints:
    - POST /api/bidding/worklogs/{id}/submit-approval/ - Submit for approval
    - POST /api/bidding/worklog-approvals/{id}/approve/ - Approve worklog
    - POST /api/bidding/worklog-approvals/{id}/reject/ - Reject worklog
    - GET /api/bidding/worklog-approvals/pending/ - Get pending approvals
    - GET /api/bidding/worklogs/{id}/approval-status/ - Get approval status
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'], url_path='submit-approval')
    def submit_approval(self, request, pk=None):
        """Submit worklog for approval"""
        try:
            approval = submit_worklog_for_approval(pk, request.user)
            serializer = WorklogApprovalSerializer(approval)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a worklog"""
        serializer = ApproveWorklogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            approval = approve_worklog(
                pk,
                request.user,
                serializer.validated_data.get('feedback')
            )
            return Response({
                'message': 'Worklog approved successfully',
                'approval': WorklogApprovalSerializer(approval).data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a worklog"""
        serializer = RejectWorklogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            approval = reject_worklog(
                pk,
                request.user,
                serializer.validated_data['feedback']
            )
            return Response({
                'message': 'Worklog rejected',
                'approval': WorklogApprovalSerializer(approval).data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending worklog approvals for current user (client)"""
        approvals = get_pending_approvals(request.user, limit=50)
        serializer = WorklogApprovalSerializer(approvals, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='approval-status')
    def approval_status(self, request, pk=None):
        """Get approval status for a worklog"""
        status_data = get_worklog_approval_status(pk)
        
        if status_data:
            return Response(status_data)
        else:
            return Response({
                'message': 'No approval request found'
            }, status=status.HTTP_404_NOT_FOUND)


class BidRetractionViewSet(viewsets.ViewSet):
    """
    ViewSet for Bid Retraction
    
    Endpoints:
    - POST /api/bidding/bids/{id}/retract/ - Retract a bid
    - GET /api/bidding/bids/{id}/can-retract/ - Check if can retract
    - GET /api/bidding/retractions/ - Get retracted bids
    - GET /api/bidding/retractions/{bid_id}/ - Get retraction details
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def retract(self, request, pk=None):
        """Retract a bid"""
        serializer = BidRetractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            retraction = retract_bid(
                pk,
                request.user,
                serializer.validated_data['reason']
            )
            return Response({
                'message': 'Bid retracted successfully',
                'retraction': RetractionDetailSerializer(retraction).data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='can-retract')
    def can_retract(self, request, pk=None):
        """Check if bid can be retracted"""
        from .models import Bid
        
        try:
            bid = Bid.objects.get(id=pk)
            can_retract, reason = can_retract_bid(bid, request.user)
            return Response({
                'can_retract': can_retract,
                'reason': reason
            })
        except Bid.DoesNotExist:
            return Response(
                {'error': 'Bid not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def list(self, request):
        """Get retracted bids for current user"""
        bids = get_retracted_bids(request.user, limit=20)
        # Use existing bid serializer
        from .serializers import BidSerializer
        serializer = BidSerializer(bids, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Get retraction details"""
        details = get_retraction_details(pk)
        
        if details:
            return Response(details)
        else:
            return Response(
                {'error': 'Retraction not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CounterOfferViewSet(viewsets.ViewSet):
    """
    ViewSet for Counter-Offers
    
    Endpoints:
    - POST /api/bidding/bids/{id}/counter-offer/ - Create counter-offer
    - POST /api/bidding/counter-offers/{id}/accept/ - Accept counter-offer
    - POST /api/bidding/counter-offers/{id}/reject/ - Reject counter-offer
    - GET /api/bidding/bids/{id}/counter-offers/ - Get counter-offers for bid
    - GET /api/bidding/counter-offers/pending/ - Get pending counter-offers
    - GET /api/bidding/counter-offers/stats/ - Get counter-offer stats
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'], url_path='counter-offer')
    def create_offer(self, request, pk=None):
        """Create a counter-offer on a bid"""
        serializer = CounterOfferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            counter_offer = create_counter_offer(
                pk,
                request.user,
                serializer.validated_data['counter_amount'],
                serializer.validated_data.get('counter_timeline'),
                serializer.validated_data.get('message')
            )
            return Response({
                'message': 'Counter-offer created successfully',
                'counter_offer': CounterOfferResponseSerializer(counter_offer).data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a counter-offer"""
        try:
            bid = accept_counter_offer(pk, request.user)
            from .serializers import BidSerializer
            return Response({
                'message': 'Counter-offer accepted',
                'bid': BidSerializer(bid).data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a counter-offer"""
        reason = request.data.get('reason', '')
        
        try:
            counter_offer = reject_counter_offer(pk, request.user, reason)
            return Response({
                'message': 'Counter-offer rejected',
                'counter_offer': CounterOfferResponseSerializer(counter_offer).data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='counter-offers')
    def list_for_bid(self, request, pk=None):
        """Get all counter-offers for a bid"""
        offers = get_counter_offers_for_bid(pk)
        serializer = CounterOfferResponseSerializer(offers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending counter-offers for current user (freelancer)"""
        offers = get_pending_counter_offers(request.user, limit=20)
        serializer = CounterOfferResponseSerializer(offers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get counter-offer statistics"""
        stats = get_counter_offer_stats(request.user)
        serializer = CounterOfferStatsSerializer(data=stats)
        serializer.is_valid()
        return Response(serializer.data)
