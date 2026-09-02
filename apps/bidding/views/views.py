from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.bidding.models import Bid, Contract
from apps.bidding.serializers import (
    BidListSerializer,
    BidDetailSerializer,
    BidCreateSerializer,
    ContractSerializer,
    ContractListSerializer,
)
from apps.bidding.services import (
    submit_bid,
    accept_bid,
    accept_contract,
    decline_contract,
    reject_bid,
    withdraw_bid,
    propose_milestone_schedule,
)
from apps.bidding.selectors import (
    get_bid_by_id,
    get_project_bids,
    get_freelancer_bids,
    get_freelancer_active_contracts,
    get_client_active_contracts,
    get_contract_by_id,
)
from apps.bidding.permissions import (
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
        ).select_related(
            'freelancer',
            'freelancer__freelancer_profile',
            'freelancer__client_profile',
            'project',
            'project__client',
            'project__client__client_profile',
            'project__client__freelancer_profile',
        ).prefetch_related('project__skills')
    
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
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if isinstance(data.get('project'), dict):
            data['project'] = data['project'].get('id') or data['project'].get('pk')

        serializer = self.get_serializer(data=data)
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
        """Accept a bid and create a contract (client only)."""
        bid = self.get_object()
        
        try:
            contract = accept_bid(
                bid_id=bid.id,
                client=request.user
            )
            return Response(
                {
                    "message": "Bid accepted and contract created successfully.",
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


class ContractViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Contract operations.

    Allowed methods: GET only (list / retrieve).
    Contracts are created exclusively via the accept_bid service and may only
    transition state through the dedicated @action endpoints below.
    Direct PATCH / PUT / DELETE are disabled to prevent financial tampering (IDOR).

    Endpoints:
    - GET  /api/contracts/              - List caller's contracts
    - GET  /api/contracts/{id}/         - Get contract detail
    - POST /api/contracts/{id}/accept_proposal/  - Accept proposal (freelancer only)
    - POST /api/contracts/{id}/decline_proposal/ - Decline proposal (freelancer only)
    """

    # ── Security: disable all mutating HTTP verbs at dispatch level ──────────
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        user = self.request.user

        if user.role == 'FREELANCER':
            return Contract.objects.filter(
                bid__freelancer=user
            ).select_related('bid__project', 'bid__freelancer')
        else:
            return Contract.objects.filter(
                bid__project__client=user
            ).select_related('bid__project', 'bid__freelancer')

    def get_serializer_class(self):
        if self.action == 'list':
            return ContractListSerializer
        return ContractSerializer

    permission_classes = [permissions.IsAuthenticated, IsContractParticipant]

    # ── Belt-and-suspenders: explicit 405 even if method list is widened ─────
    def create(self, request, *args, **kwargs):
        return Response(
            {"error": "Contracts cannot be created directly.", "code": "method_not_allowed"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {"error": "Contracts cannot be modified directly.", "code": "method_not_allowed"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"error": "Contracts cannot be modified directly.", "code": "method_not_allowed"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"error": "Contracts cannot be deleted directly.", "code": "method_not_allowed"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=['post'])
    def accept_proposal(self, request, pk=None):
        """Accept a contract proposal (freelancer only)."""
        try:
            contract = accept_contract(pk, request.user)
            return Response(
                {
                    "message": "Contract proposal accepted successfully.",
                    "contract": ContractSerializer(contract).data
                },
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def decline_proposal(self, request, pk=None):
        """Decline a contract proposal (freelancer only)."""
        try:
            decline_contract(pk, request.user)
            return Response(
                {"message": "Contract proposal declined and deleted successfully."},
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def propose_milestones(self, request, pk=None):
        """Propose milestone schedule for a contract (client only)."""
        milestones_list = request.data.get("milestones")
        try:
            contract = propose_milestone_schedule(
                contract_id=pk,
                client=request.user,
                milestones_list=milestones_list
            )
            return Response(
                {
                    "message": "Milestone schedule proposed successfully.",
                    "contract": ContractSerializer(contract).data,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
