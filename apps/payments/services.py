import razorpay
import hmac
import hashlib
from django.db import transaction
from django.conf import settings
from django.utils import timezone

from .models import Payment, Escrow, PlatformEarning, PaymentEvent
from apps.bidding.models import Contract
from apps.projects.services import mark_project_completed
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError
from core.utils import calculate_platform_cut


razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_escrow(contract: Contract, client) -> Payment:
    """
    Create escrow payment for a contract.
    Client pays full amount which is held in escrow.
    
    Args:
        contract: Contract instance
        client: User instance (must be contract client)
    
    Returns:
        Created Payment instance with Razorpay order details
    """
    if contract.client != client:
        raise PermissionDeniedError("Only the client can create escrow.")
    
    if hasattr(contract, 'payment'):
        raise ValidationError("Payment already exists for this contract.")
    
    with transaction.atomic():
        # Create Razorpay Order
        try:
            order_data = {
                'amount': int(contract.agreed_amount * 100),  # Convert to paise (smallest currency unit)
                'currency': 'INR',
                'receipt': f'contract_{contract.id}',
                'notes': {
                    'contract_id': contract.id,
                    'project_title': contract.bid.project.title,
                }
            }
            razorpay_order = razorpay_client.order.create(data=order_data)
        except razorpay.errors.BadRequestError as e:
            raise ValidationError(f"Payment processing error: {str(e)}")
        
        # Create payment record
        payment = Payment.objects.create(
            contract=contract,
            total_amount=contract.agreed_amount,
            status=Payment.Status.PENDING,
            razorpay_order_id=razorpay_order['id'],
        )
        
        return payment


def confirm_escrow_payment(razorpay_order_id: str, razorpay_payment_id: str) -> Payment:
    """
    Confirm that escrow payment has been received (called by webhook or after payment verification).
    
    Args:
        razorpay_order_id: Razorpay Order ID
        razorpay_payment_id: Razorpay Payment ID
    
    Returns:
        Updated Payment instance
    """
    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(
                razorpay_order_id=razorpay_order_id
            )
        except Payment.DoesNotExist:
            raise NotFoundError("Payment not found.")
        
        if payment.status != Payment.Status.PENDING:
            raise ValidationError("Payment is not pending.")
        
        # Update payment status
        payment.status = Payment.Status.ESCROWED
        payment.razorpay_payment_id = razorpay_payment_id
        payment.save()
        
        # Create escrow record
        Escrow.objects.create(
            payment=payment,
            held_amount=payment.total_amount,
        )
        
        return payment


def release_payment(contract: Contract, client) -> Payment:
    """
    Release payment to freelancer (minus platform cut).
    
    Args:
        contract: Contract instance
        client: User instance (must be contract client)
    
    Returns:
        Updated Payment instance
    """
    from apps.notifications.tasks import (
        notify_freelancer_payment_released,
        generate_delivery_proof,
    )
    
    if contract.client != client:
        raise PermissionDeniedError("Only the client can release payment.")
    
    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(contract=contract)
        except Payment.DoesNotExist:
            raise NotFoundError("Payment not found.")
        
        if payment.status != Payment.Status.ESCROWED:
            raise ValidationError("Payment is not in escrow.")
        
        # Calculate platform cut
        cut_info = calculate_platform_cut(
            payment.total_amount,
            settings.PLATFORM_CUT_PERCENTAGE
        )
        
        # Create platform earning record
        PlatformEarning.objects.create(
            payment=payment,
            cut_percentage=cut_info['cut_percentage'],
            cut_amount=cut_info['cut_amount'],
        )
        
        # Update payment status
        payment.status = Payment.Status.RELEASED
        payment.save()
        
        # Update escrow record
        escrow = payment.escrow
        escrow.released_at = timezone.now()
        escrow.save()
        
        # Complete the contract
        contract.is_active = False
        contract.end_date = timezone.now()
        contract.save()
        
        # Mark project as completed
        mark_project_completed(contract.bid.project)
        
        # Schedule post-release tasks
        transaction.on_commit(lambda: [
            razorpay_transfer_to_freelancer_task.delay(
                payment.id,
                float(cut_info['freelancer_amount'])
            ),
            notify_freelancer_payment_released.delay(contract.id),
            generate_delivery_proof.delay(contract.id),
        ])
        
        return payment


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Verify Razorpay payment signature.
    
    Args:
        order_id: Razorpay Order ID
        payment_id: Razorpay Payment ID
        signature: Razorpay signature
    
    Returns:
        True if signature is valid
    """
    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(generated_signature, signature)


def process_razorpay_webhook(payload: dict, raw_body: bytes, signature: str) -> bool:
    """
    Process Razorpay webhook event with signature verification.
    
    Args:
        payload: Request body (dict)
        raw_body: Raw request body (bytes) - required for signature verification
        signature: Razorpay signature header
    
    Returns:
        True if processed successfully
    """
    from .tasks import process_razorpay_webhook_task
    
    # Verify webhook signature using raw request body
    try:
        razorpay_client.utility.verify_webhook_signature(
            raw_body,
            signature,
            settings.RAZORPAY_WEBHOOK_SECRET
        )
    except razorpay.errors.SignatureVerificationError:
        raise PermissionDeniedError("Invalid signature")
    
    event_id = payload.get('event')
    
    # Check idempotency
    if has_payment_event_been_processed(event_id):
        return True
    
    # Process event asynchronously
    process_razorpay_webhook_task.delay(
        event_id,
        payload.get('event'),
        payload.get('payload')
    )
    
    return True


def has_payment_event_been_processed(razorpay_event_id: str) -> bool:
    """Check if event has been processed."""
    return PaymentEvent.objects.filter(razorpay_event_id=razorpay_event_id).exists()


def record_payment_event(payment: Payment, razorpay_event_id: str, event_type: str):
    """Record processed payment event for idempotency."""
    PaymentEvent.objects.create(
        payment=payment,
        razorpay_event_id=razorpay_event_id,
        event_type=event_type,
    )



def process_contract_termination_payment(
    payment,
    refund_percentage: float
) -> None:
    """
    Process payment for terminated contract.
    
    Args:
        payment: Payment instance
        refund_percentage: Percentage to refund to client (0-100)
    """
    from decimal import Decimal
    
    if payment.status != Payment.Status.ESCROWED:
        raise ValidationError("Payment is not in escrow.")
    
    refund_amount = payment.total_amount * Decimal(refund_percentage / 100)
    freelancer_amount = payment.total_amount - refund_amount
    
    with transaction.atomic():
        # Update payment status
        payment.status = Payment.Status.REFUNDED if refund_percentage == 100 else Payment.Status.PARTIALLY_REFUNDED
        payment.refund_amount = refund_amount
        payment.save()
        
        # Update escrow
        escrow = payment.escrow
        escrow.released_at = timezone.now()
        escrow.refund_amount = refund_amount
        escrow.save()
        
        # Process refund if any
        if refund_amount > 0:
            # Schedule refund task
            transaction.on_commit(
                lambda: process_razorpay_refund_task.delay(
                    payment.id,
                    float(refund_amount)
                )
            )
        
        # Process freelancer payment if any
        if freelancer_amount > 0:
            cut_info = calculate_platform_cut(
                freelancer_amount,
                settings.PLATFORM_CUT_PERCENTAGE
            )
            
            PlatformEarning.objects.create(
                payment=payment,
                cut_percentage=cut_info['cut_percentage'],
                cut_amount=cut_info['cut_amount'],
            )
            
            transaction.on_commit(
                lambda: razorpay_transfer_to_freelancer_task.delay(
                    payment.id,
                    float(cut_info['freelancer_amount'])
                )
            )


def process_refund(
    payment_id: int,
    refund_amount: float,
    reason: str = "Contract termination"
) -> dict:
    """
    Process a refund for a payment.
    
    Args:
        payment_id: Payment ID
        refund_amount: Amount to refund
        reason: Refund reason
    
    Returns:
        Refund details
    """
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        raise NotFoundError("Payment not found.")
    
    if not payment.razorpay_payment_id:
        raise ValidationError("No payment ID found for refund.")
    
    try:
        # Create refund via Razorpay
        refund = razorpay_client.payment.refund(
            payment.razorpay_payment_id,
            {
                'amount': int(refund_amount * 100),  # Convert to paise
                'notes': {
                    'reason': reason,
                    'payment_id': payment.id,
                }
            }
        )
        
        # Record refund
        payment.refund_amount = refund_amount
        payment.razorpay_refund_id = refund['id']
        payment.save()
        
        return refund
        
    except razorpay.errors.BadRequestError as e:
        raise ValidationError(f"Refund processing error: {str(e)}")


def initiate_payment_dispute(
    payment_id: int,
    disputer: User,
    reason: str,
    description: str,
) -> dict:
    """
    Initiate a payment dispute.
    
    Args:
        payment_id: Payment ID
        disputer: User initiating dispute
        reason: Dispute reason
        description: Detailed description
    
    Returns:
        Dispute details
    """
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        raise NotFoundError("Payment not found.")
    
    contract = payment.contract
    
    # Verify disputer is part of contract
    if disputer not in [contract.bid.freelancer, contract.bid.project.client]:
        raise PermissionDeniedError("You are not part of this contract.")
    
    # Check if dispute already exists
    if hasattr(payment, 'dispute'):
        raise ValidationError("Dispute already exists for this payment.")
    
    from .models_dispute import PaymentDispute
    
    with transaction.atomic():
        dispute = PaymentDispute.objects.create(
            payment=payment,
            disputer=disputer,
            reason=reason,
            description=description,
            status=PaymentDispute.Status.OPEN,
        )
        
        # Notify the other party
        other_party = (
            contract.bid.project.client 
            if disputer == contract.bid.freelancer 
            else contract.bid.freelancer
        )
        
        from apps.notifications.services import create_notification
        create_notification(
            recipient=other_party,
            title="Payment Dispute Initiated",
            body=f"{disputer.get_full_name()} has initiated a payment dispute.",
            type="PAYMENT_DISPUTE",
            data={
                "payment_id": payment.id,
                "dispute_id": dispute.id
            }
        )
        
        # Notify admin
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            create_notification(
                recipient=admin,
                title="New Payment Dispute",
                body=f"Payment dispute initiated for contract {contract.id}.",
                type="PAYMENT_DISPUTE_ADMIN",
                data={
                    "payment_id": payment.id,
                    "dispute_id": dispute.id
                }
            )
        
        return {
            'dispute_id': dispute.id,
            'status': dispute.status,
            'created_at': dispute.created_at,
        }
