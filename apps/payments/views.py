from django.db.models import Sum, Q
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentListSerializer,
    CreateEscrowSerializer,
    ReleasePaymentSerializer,
    PaymentHistorySerializer,
)
from .services import (
    create_escrow,
    confirm_escrow_payment,
    release_payment,
    process_razorpay_webhook,
    verify_razorpay_signature,
)
from .selectors import (
    get_payment_by_id,
    get_payment_by_contract,
    get_client_payment_history,
    get_freelancer_earnings,
    get_client_total_spent,
    get_freelancer_total_earned,
)
from .permissions import IsPaymentParticipant, IsPaymentClient
from apps.bidding.models import Contract
from core.exceptions import ValidationError


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Payment operations.
    
    Endpoints:
    - GET /api/payments/ - List user's payments
    - GET /api/payments/{id}/ - Get payment detail
    - POST /api/payments/escrow/ - Create escrow (client only)
    - POST /api/payments/release/ - Release payment (client only)
    """
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'CLIENT':
            return get_client_payment_history(user)
        else:
            return get_freelancer_earnings(user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PaymentListSerializer
        return PaymentSerializer
    
    permission_classes = [permissions.IsAuthenticated, IsPaymentParticipant]
    
    @action(detail=False, methods=['post'])
    def escrow(self, request):
        """Create escrow for a contract (client only)."""
        serializer = CreateEscrowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            contract = Contract.objects.get(
                id=serializer.validated_data['contract_id']
            )
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found.", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            payment = create_escrow(contract, request.user)
            return Response(
                {
                    "message": "Escrow created successfully.",
                    "payment": PaymentSerializer(payment).data,
                    "razorpay_order_id": payment.razorpay_order_id,
                    "amount": int(payment.total_amount * 100),  # Amount in paise
                    "currency": "INR",
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=False, methods=['post'])
    def release(self, request):
        """Release payment to freelancer (client only)."""
        serializer = ReleasePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            contract = Contract.objects.get(
                id=serializer.validated_data['contract_id']
            )
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found.", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            payment = release_payment(contract, request.user)
            return Response(
                {
                    "message": "Payment released successfully.",
                    "payment": PaymentSerializer(payment).data,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get payment history summary."""
        user = request.user
        
        if user.role == 'CLIENT':
            total_spent = get_client_total_spent(user)
            pending_escrow = Payment.objects.filter(
                contract__bid__project__client=user,
                status=Payment.Status.ESCROWED
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            data = {
                'total_spent': total_spent,
                'total_earned': 0,
                'pending_escrow': pending_escrow,
            }
        else:
            total_earned = get_freelancer_total_earned(user)
            
            data = {
                'total_spent': 0,
                'total_earned': total_earned,
                'pending_escrow': 0,
            }
        
        serializer = PaymentHistorySerializer(data)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_payment(request):
    """
    Verify Razorpay payment after client completes payment on frontend.
    """
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_signature = request.data.get('razorpay_signature')
    
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return Response(
            {"error": "Missing payment verification data", "code": "invalid_data"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    try:
        # Verify signature
        if not verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
            return Response(
                {"error": "Invalid payment signature", "code": "invalid_signature"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Confirm escrow payment
        payment = confirm_escrow_payment(razorpay_order_id, razorpay_payment_id)
        
        return Response(
            {
                "message": "Payment verified successfully.",
                "payment": PaymentSerializer(payment).data,
            },
            status=status.HTTP_200_OK,
        )
    except ValidationError as e:
        return Response(
            {"error": e.message, "code": e.code},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def razorpay_webhook(request):
    """
    Razorpay webhook endpoint for payment events.
    """
    import json
    
    # Get raw body for signature verification
    raw_body = request.body
    payload = json.loads(raw_body)
    sig_header = request.headers.get('X-Razorpay-Signature')
    
    try:
        process_razorpay_webhook(payload, raw_body, sig_header)
        return Response({"status": "success"}, status=status.HTTP_200_OK)
    except ValidationError as e:
        return Response(
            {"error": e.message, "code": e.code},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
