from django.db.models import QuerySet, Sum
from django.shortcuts import get_object_or_404
from .models import Payment, Escrow, PlatformEarning, PaymentEvent


def get_payment_by_id(payment_id: int) -> Payment:
    """Get payment by ID."""
    return get_object_or_404(Payment, id=payment_id)


def get_payment_by_contract(contract_id: int) -> Payment | None:
    """Get payment by contract ID."""
    try:
        return Payment.objects.get(contract_id=contract_id)
    except Payment.DoesNotExist:
        return None


def get_client_payment_history(client) -> QuerySet[Payment]:
    """Get all payments made by a client."""
    return Payment.objects.filter(
        contract__bid__project__client=client
    ).select_related('contract__bid__project')


def get_freelancer_earnings(freelancer) -> QuerySet[Payment]:
    """Get all payments received by a freelancer."""
    return Payment.objects.filter(
        contract__bid__freelancer=freelancer,
        status=Payment.Status.RELEASED
    ).select_related('contract__bid__project')


def get_freelancer_total_earned(freelancer) -> float:
    """Get total earnings for a freelancer."""
    result = Payment.objects.filter(
        contract__bid__freelancer=freelancer,
        status=Payment.Status.RELEASED
    ).aggregate(total=Sum('total_amount'))
    return result['total'] or 0


def get_client_total_spent(client) -> float:
    """Get total amount spent by a client."""
    result = Payment.objects.filter(
        contract__bid__project__client=client,
        status__in=[Payment.Status.ESCROWED, Payment.Status.RELEASED]
    ).aggregate(total=Sum('total_amount'))
    return result['total'] or 0


def get_platform_total_earnings() -> float:
    """Get total platform earnings."""
    result = PlatformEarning.objects.aggregate(total=Sum('cut_amount'))
    return result['total'] or 0


def has_payment_event_been_processed(razorpay_event_id: str) -> bool:
    """Check if a Razorpay event has already been processed."""
    return PaymentEvent.objects.filter(razorpay_event_id=razorpay_event_id).exists()


def get_escrow_by_payment(payment_id: int) -> Escrow | None:
    """Get escrow record for a payment."""
    try:
        return Escrow.objects.get(payment_id=payment_id)
    except Escrow.DoesNotExist:
        return None
