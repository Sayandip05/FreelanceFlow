from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Bid, Contract
from .serializers import (
    BidListSerializer,
    BidDetailSerializer,
    BidCreateSerializer,
    ContractSerializer,
    ContractListSerializer,
)
from .services import (
    submit_bid,
    accept_bid,
    reject_bid,
    withdraw_bid,
)
from .selectors import (
    get_bid_by_id,
    get_project_bids,
    get_freelancer_bids,
    get_freelancer_active_contracts,
    get_client_active_contracts,
    get_contract_by_id,
)
from .permissions import (
    IsBidOwner,
    IsProjectClient,
    IsContractParticipant,
)
from apps.users.permissions import IsFreelancer, IsClient
from core.exceptions import ValidationError


class BidViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Bid operations.
    
    Endpoints:
    - GET /api/bids/ - List user's bids (freelancer) or project bids (client)
    - POST /api/bids/ - Submit a bid (freelancers only)
    - GET /api/bids/{id}/ - Get bid detail
    - DELETE /api/bids/{id}/ - Withdraw bid (freelancer only)
    - POST /api/bids/{id}/accept/ - Accept bid (client only)
    - POST /api/bids/{id}/reject/ - Reject bid (client only)
    """
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'FREELANCER':
            return get_freelancer_bids(user)
        
        # For clients, return bids on their projects
        return Bid.objects.filter(
            project__client=user
        ).select_related('freelancer', 'project')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BidCreateSerializer
        elif self.action == 'list':
            return BidListSerializer
        return BidDetailSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsFreelancer()]
        elif self.action == 'destroy':
            return [permissions.IsAuthenticated(), IsBidOwner()]
        elif self.action in ['accept', 'reject']:
            return [permissions.IsAuthenticated(), IsProjectClient()]
        return [permissions.IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            bid = submit_bid(
                freelancer=request.user,
                project_id=serializer.validated_data['project'].id,
                amount=serializer.validated_data['amount'],
                cover_letter=serializer.validated_data['cover_letter'],
            )
            
            return Response(
                BidDetailSerializer(bid).data,
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    def destroy(self, request, *args, **kwargs):
        bid = self.get_object()
        
        try:
            withdraw_bid(bid.id, request.user)
            return Response(
                {"message": "Bid withdrawn successfully."},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a bid (client only)."""
        bid = self.get_object()
        
        try:
            contract = accept_bid(bid.id, request.user)
            return Response(
                {
                    "message": "Bid accepted successfully.",
                    "contract": ContractSerializer(contract).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a bid (client only)."""
        bid = self.get_object()
        
        try:
            reject_bid(bid.id, request.user)
            return Response(
                {"message": "Bid rejected successfully."},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=False, methods=['get'])
    def my_bids(self, request):
        """Get current freelancer's bids."""
        if request.user.role != 'FREELANCER':
            return Response(
                {"error": "Only freelancers have bids.", "code": "permission_denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        bids = get_freelancer_bids(request.user)
        serializer = BidListSerializer(bids, many=True)
        return Response(serializer.data)


class ContractViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Contract operations (read-only).
    
    Endpoints:
    - GET /api/contracts/ - List user's contracts
    - GET /api/contracts/{id}/ - Get contract detail
    """
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'FREELANCER':
            return get_freelancer_active_contracts(user)
        else:
            return get_client_active_contracts(user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ContractListSerializer
        return ContractSerializer
    
    permission_classes = [permissions.IsAuthenticated, IsContractParticipant]
