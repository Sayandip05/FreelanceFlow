import razorpay
import hmac
import hashlib
import logging
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.payments.models import Payment, Escrow, PlatformEarning, PaymentEvent
from apps.bidding.models import Contract
from apps.projects.services import mark_project_completed
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError
from core.utils import calculate_platform_cut
User = get_user_model()
logger = logging.getLogger("apps.payments")


def __getattr__(name):
    """Lazy module-level attribute access for avoiding circular imports."""
    if name == "process_razorpay_webhook_task":
        from apps.payments.tasks import process_razorpay_webhook_task
        return process_razorpay_webhook_task
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")



def _get_razorpay_client():
    """
    Lazily construct the Razorpay client so it is only instantiated when an
    actual API call is made.  This prevents startup crashes when credentials
    are not yet set (e.g. during unit tests or Django management commands).
    """
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def create_milestone_escrow(contract: Contract, client, milestone) -> Payment:
    """
    Create escrow payment for a specific milestone.
    Client pays milestone amount which is held in escrow.
    """
    if contract.client != client:
        raise PermissionDeniedError("Only the client can fund a milestone.")

    if milestone.contract != contract:
        raise ValidationError("Milestone does not belong to this contract.")

    # Check if a payment record already exists for this milestone
    if hasattr(milestone, 'payment_record'):
        if milestone.payment_record.status == Payment.Status.PENDING:
            return milestone.payment_record
        raise ValidationError("Payment already exists or is in progress for this milestone.")

    logger.info(
        "Creating Razorpay escrow order for milestone: contract_id=%s milestone_id=%s amount=%s",
        contract.id, milestone.id, milestone.amount,
    )

    razorpay_order = None
    try:
        order_data = {
            'amount': int(milestone.amount * 100),  # paise
            'currency': 'INR',
            'receipt': f'milestone_{milestone.id}',
            'notes': {
                'contract_id': contract.id,
                'milestone_id': milestone.id,
                'project_title': contract.bid.project.title,
                'milestone_title': milestone.title
            },
        }
        razorpay_order = _get_razorpay_client().order.create(data=order_data)
    except Exception as e:
        logger.warning(
            "Razorpay order creation failed for milestone: milestone_id=%s error=%s. Falling back to mock simulation.",
            milestone.id, str(e),
        )

    if razorpay_order:
        with transaction.atomic():
            payment = Payment.objects.create(
                contract=contract,
                milestone=milestone,
                total_amount=milestone.amount,
                status=Payment.Status.PENDING,
                razorpay_order_id=razorpay_order['id'],
            )
        logger.info(
            "Milestone escrow payment record created: payment_id=%s order_id=%s",
            payment.id, payment.razorpay_order_id,
        )
        return payment
    else:
        # Generate mock order details and confirm immediately
        import uuid
        mock_order_id = f"order_mock_{uuid.uuid4().hex[:12]}"
        mock_payment_id = f"pay_mock_{uuid.uuid4().hex[:12]}"
        
        with transaction.atomic():
            payment = Payment.objects.create(
                contract=contract,
                milestone=milestone,
                total_amount=milestone.amount,
                status=Payment.Status.PENDING,
                razorpay_order_id=mock_order_id,
            )
        confirm_escrow_payment(mock_order_id, mock_payment_id)
        logger.info(
            "Mock milestone escrow payment created and confirmed immediately: milestone_id=%s payment_id=%s",
            milestone.id, payment.id
        )
        return payment


def create_escrow(contract: Contract, client) -> Payment:
    """
    Create escrow payment for a contract (non-milestone legacy fallback).
    Client pays full amount which is held in escrow.
    """
    if contract.client != client:
        raise PermissionDeniedError("Only the client can create escrow.")

    if contract.payments.filter(milestone__isnull=True).exists():
        raise ValidationError("Payment already exists for this contract.")

    logger.info(
        "Creating Razorpay escrow order: contract_id=%s client_id=%s amount=%s",
        contract.id, client.id, contract.agreed_amount,
    )

    razorpay_order = None
    try:
        order_data = {
            'amount': int(contract.agreed_amount * 100),  # paise
            'currency': 'INR',
            'receipt': f'contract_{contract.id}',
            'notes': {
                'contract_id': contract.id,
                'project_title': contract.bid.project.title,
            },
        }
        razorpay_order = _get_razorpay_client().order.create(data=order_data)
    except Exception as e:
        logger.warning(
            "Razorpay order creation failed: contract_id=%s error=%s. Falling back to mock simulation.",
            contract.id, str(e),
        )

    if razorpay_order:
        with transaction.atomic():
            payment = Payment.objects.create(
                contract=contract,
                total_amount=contract.agreed_amount,
                status=Payment.Status.PENDING,
                razorpay_order_id=razorpay_order['id'],
            )
        logger.info(
            "Escrow payment record created: payment_id=%s order_id=%s",
            payment.id, payment.razorpay_order_id,
        )
        return payment
    else:
        # Generate mock order details and confirm immediately
        import uuid
        mock_order_id = f"order_mock_{uuid.uuid4().hex[:12]}"
        mock_payment_id = f"pay_mock_{uuid.uuid4().hex[:12]}"
        
        with transaction.atomic():
            payment = Payment.objects.create(
                contract=contract,
                total_amount=contract.agreed_amount,
                status=Payment.Status.PENDING,
                razorpay_order_id=mock_order_id,
            )
        confirm_escrow_payment(mock_order_id, mock_payment_id)
        logger.info(
            "Mock escrow payment created and confirmed immediately: contract_id=%s payment_id=%s",
            contract.id, payment.id
        )
        return payment


def confirm_escrow_payment(razorpay_order_id: str, razorpay_payment_id: str) -> Payment:
    """
    Confirm that escrow payment has been received (called by webhook or after payment verification).
    """
    from apps.payments.models.models_milestone import PaymentMilestone
    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(
                razorpay_order_id=razorpay_order_id
            )
        except Payment.DoesNotExist:
            logger.error(
                "confirm_escrow_payment: order_id=%s not found in DB",
                razorpay_order_id,
            )
            raise NotFoundError("Payment not found.")

        if payment.status != Payment.Status.PENDING:
            logger.warning(
                "confirm_escrow_payment: payment_id=%s already in status=%s, skipping",
                payment.id, payment.status,
            )
            raise ValidationError("Payment is not pending.")

        payment.status = Payment.Status.ESCROWED
        payment.razorpay_payment_id = razorpay_payment_id
        payment.save()

        Escrow.objects.create(
            payment=payment,
            held_amount=payment.total_amount,
        )

        if payment.milestone:
            milestone = payment.milestone
            milestone.status = PaymentMilestone.Status.IN_PROGRESS
            milestone.save()

        from apps.notifications.services import notify_escrow_created
        contract = payment.contract
        transaction.on_commit(
            lambda: notify_escrow_created(
                freelancer=contract.bid.freelancer,
                project_title=contract.bid.project.title,
                amount=float(payment.total_amount),
            )
        )

    logger.info(
        "Escrow confirmed: payment_id=%s razorpay_payment_id=%s amount=%s",
        payment.id, razorpay_payment_id, payment.total_amount,
    )
    return payment


def release_payment(contract: Contract, client, payment_id: int = None) -> Payment:
    """
    Release payment to freelancer (minus platform cut).
    """
    from apps.payments.tasks import razorpay_transfer_to_freelancer_task
    if contract.client != client:
        raise PermissionDeniedError("Only the client can release payment.")

    fund_account_id = getattr(
        getattr(contract.bid.freelancer, "freelancer_profile", None),
        "razorpay_fund_account_id",
        "",
    )

    is_placeholder_keys = (
        not getattr(settings, "RAZORPAY_KEY_ID", "") or 
        settings.RAZORPAY_KEY_ID.startswith("rzp_test_placeholder") or
        settings.RAZORPAY_KEY_ID == "your_razorpay_key_id"
    )
    
    use_simulation = is_placeholder_keys or not fund_account_id or not getattr(settings, "RAZORPAY_ACCOUNT_NUMBER", "")

    if use_simulation:
        with transaction.atomic():
            try:
                if payment_id:
                    payment = Payment.objects.select_for_update().get(id=payment_id, contract=contract)
                else:
                    payment = Payment.objects.select_for_update().get(contract=contract)
            except Payment.DoesNotExist:
                raise NotFoundError("Payment not found.")

            if payment.status != Payment.Status.ESCROWED:
                raise ValidationError("Payment is not in escrow.")

            cut_info = calculate_platform_cut(
                payment.total_amount,
                settings.PLATFORM_CUT_PERCENTAGE
            )

            # Update Payment status
            payment.status = Payment.Status.RELEASED
            payment.razorpay_payout_id = "payout_mock_simulated"
            payment.save()

            # Record Platform Earning
            PlatformEarning.objects.get_or_create(
                payment=payment,
                defaults={
                    "cut_percentage": cut_info["cut_percentage"],
                    "cut_amount": cut_info["cut_amount"],
                },
            )

            # Update Escrow
            if hasattr(payment, 'escrow'):
                escrow = payment.escrow
                escrow.released_at = timezone.now()
                escrow.save()

            # If milestone payment, update milestone status to PAID
            if payment.milestone:
                milestone = payment.milestone
                milestone.status = milestone.Status.PAID
                milestone.paid_at = timezone.now()
                milestone.save()

            # Check if all contract milestones are paid to close contract
            from apps.payments.models.models_milestone import PaymentMilestone
            all_milestones = PaymentMilestone.objects.filter(contract=contract)
            if all_milestones.exists() and all(m.status == PaymentMilestone.Status.PAID for m in all_milestones):
                contract.is_active = False
                contract.end_date = timezone.now()
                contract.save()
                from apps.projects.models import Project
                from apps.projects.services import mark_project_completed
                if contract.bid.project.status == Project.Status.IN_PROGRESS:
                    mark_project_completed(contract.bid.project)
            elif not all_milestones.exists():
                contract.is_active = False
                contract.end_date = timezone.now()
                contract.save()
                from apps.projects.models import Project
                from apps.projects.services import mark_project_completed
                if contract.bid.project.status == Project.Status.IN_PROGRESS:
                    mark_project_completed(contract.bid.project)

        # Trigger notification & delivery proof generation
        try:
            from apps.notifications.services import create_notification
            from apps.notifications.models import Notification
            create_notification(
                recipient=contract.bid.freelancer,
                title="Payment Released",
                body=f"Payment for {contract.bid.project.title} has been released.",
                notification_type=Notification.Type.PAYMENT_RELEASED,
            )
        except Exception as e:
            logger.warning("Failed to create notification: %s", str(e))

        try:
            from apps.worklogs.services import generate_delivery_proof
            generate_delivery_proof(contract.id)
        except Exception as e:
            logger.warning("Failed to generate delivery proof: %s", str(e))

        logger.info(
            "Mock payout simulated successfully: payment_id=%s contract_id=%s amount=%s",
            payment.id, contract.id, payment.total_amount
        )
        return payment

    # Real path when keys and accounts are configured
    if not settings.RAZORPAY_ACCOUNT_NUMBER:
        raise ValidationError("Razorpay account number is not configured for payouts.")

    if not fund_account_id:
        raise ValidationError("Freelancer payout account is not configured.")

    with transaction.atomic():
        try:
            if payment_id:
                payment = Payment.objects.select_for_update().get(id=payment_id, contract=contract)
            else:
                payment = Payment.objects.select_for_update().get(contract=contract)
        except Payment.DoesNotExist:
            raise NotFoundError("Payment not found.")

        if payment.status != Payment.Status.ESCROWED:
            raise ValidationError("Payment is not in escrow.")

        cut_info = calculate_platform_cut(
            payment.total_amount,
            settings.PLATFORM_CUT_PERCENTAGE
        )

        payment.status = Payment.Status.PAYOUT_PENDING
        payment.payout_error = ""
        payment.save()

        logger.info(
            "Payment release initiated: payment_id=%s contract_id=%s "
            "freelancer_id=%s amount=%s platform_cut=%s",
            payment.id, contract.id,
            contract.bid.freelancer.id,
            cut_info['freelancer_amount'],
            cut_info['cut_amount'],
        )

        def after_commit():
            razorpay_transfer_to_freelancer_task.delay(
                payment.id,
                float(cut_info['freelancer_amount'])
            )

        transaction.on_commit(after_commit)

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


def process_razorpay_webhook(
    payload: dict,
    raw_body: bytes,
    signature: str,
    event_id: str | None = None,
) -> bool:
    """
    Process Razorpay webhook event with signature verification.
    
    Args:
        payload: Request body (dict)
        raw_body: Raw request body (bytes) - required for signature verification
        signature: Razorpay signature header
        event_id: Unique Razorpay webhook event ID header
    
    Returns:
        True if processed successfully
    """
    import apps.payments.tasks as _payment_tasks
    # Verify webhook signature using raw request body
    # Razorpay's verify_webhook_signature expects a string, not bytes
    body_str = raw_body.decode('utf-8') if isinstance(raw_body, bytes) else raw_body
    try:
        _get_razorpay_client().utility.verify_webhook_signature(
            body_str,
            signature,
            settings.RAZORPAY_WEBHOOK_SECRET
        )
    except razorpay.errors.SignatureVerificationError:
        raise PermissionDeniedError("Invalid signature")
    
    if not event_id:
        raise ValidationError("Missing Razorpay event ID.")
    
    event_type = payload.get('event')
    
    # Check idempotency
    if has_payment_event_been_processed(event_id):
        return True
    
    # Process event asynchronously via module reference (allows mocking in tests)
    _payment_tasks.process_razorpay_webhook_task.delay(
        event_id,
        event_type,
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

    # Use Decimal arithmetic throughout to avoid floating-point precision loss.
    refund_amount = payment.total_amount * (
        Decimal(str(refund_percentage)) / Decimal('100')
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    freelancer_amount = payment.total_amount - refund_amount
    
    with transaction.atomic():
        # Update payment status
        payment.status = Payment.Status.REFUNDED
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
            from apps.payments.tasks import process_razorpay_refund_task
            transaction.on_commit(
                lambda: process_razorpay_refund_task.delay(
                    payment.id,
                    float(refund_amount)
                )
            )
        
        # Process freelancer payment if any
        if freelancer_amount > 0:
            from apps.payments.tasks import razorpay_transfer_to_freelancer_task
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
        refund = _get_razorpay_client().payment.refund(
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
    
    from apps.payments.models.models_dispute import PaymentDispute
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
            notification_type="PAYMENT_DISPUTE",
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
                notification_type="PAYMENT_DISPUTE_ADMIN",
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
