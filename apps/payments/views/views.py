import logging

from django.db.models import Sum, Q
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from apps.payments.models import Payment
from apps.payments.serializers import (
    PaymentSerializer,
    PaymentListSerializer,
    CreateEscrowSerializer,
    ReleasePaymentSerializer,
    PaymentHistorySerializer,
)
from apps.payments.services import (
    create_escrow,
    confirm_escrow_payment,
    release_payment,
    process_razorpay_webhook,
    verify_razorpay_signature,
)
from apps.payments.selectors import (
    get_payment_by_id,
    get_payment_by_contract,
    get_client_payment_history,
    get_freelancer_earnings,
    get_client_total_spent,
    get_freelancer_total_earned,
)
from apps.payments.permissions import IsPaymentParticipant, IsPaymentClient
from apps.bidding.models import Contract
from core.exceptions import ValidationError
logger = logging.getLogger("apps.payments.views")


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
        # Only clients can initiate escrow payments
        if not hasattr(request.user, 'role') or request.user.role != 'CLIENT':
            return Response(
                {"error": "Only clients can initiate escrow payments.", "code": "permission_denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

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
                    "currency": "USD",
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
                    "message": "Payment release initiated successfully.",
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

    IMPORTANT: Razorpay retries webhooks that do not receive HTTP 200.
    - Invalid signature  → log and return 200 (do nothing, but don't retry).
    - Missing event ID   → 400 so Razorpay retries with a corrected payload.
    - Any other error    → 200 (logged internally) to avoid infinite retries.
    """
    import json
    from core.exceptions import PermissionDeniedError
    raw_body = request.body
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return Response(
            {"error": "Invalid JSON payload", "code": "invalid_payload"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    sig_header = request.headers.get('X-Razorpay-Signature')
    event_id = request.headers.get('X-Razorpay-Event-Id')

    try:
        process_razorpay_webhook(payload, raw_body, sig_header, event_id)
        return Response({"status": "success"}, status=status.HTTP_200_OK)

    except PermissionDeniedError:
        # Invalid signature — log the attempt and acknowledge so Razorpay
        # doesn't retry (retries on non-200 would flood our endpoint).
        logger.warning(
            "Razorpay webhook rejected: invalid signature. "
            "event_id=%s sig=%s",
            event_id,
            sig_header,
        )
        return Response(
            {"status": "ignored", "reason": "invalid_signature"},
            status=status.HTTP_200_OK,
        )

    except ValidationError as e:
        # Missing or malformed event ID — tell Razorpay to retry.
        return Response(
            {"error": e.message, "code": e.code},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        logger.exception("Unexpected error processing Razorpay webhook: %s", e)
        # Return 200 so Razorpay doesn't flood us with retries.
        return Response(
            {"status": "error", "reason": "internal_error"},
            status=status.HTTP_200_OK,
        )
