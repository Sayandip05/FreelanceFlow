"""
Multi-Currency Services
Handles currency conversion and multi-currency payments
"""
from django.db import transaction
from decimal import Decimal
from .models_extended import CurrencyExchangeRate, MultiCurrencyPayment


def get_exchange_rate(from_currency, to_currency):
    """Get current exchange rate"""
    try:
        rate = CurrencyExchangeRate.objects.get(
            from_currency=from_currency,
            to_currency=to_currency
        )
        return rate.rate
    except CurrencyExchangeRate.DoesNotExist:
        return Decimal('1.0')


@transaction.atomic
def convert_currency(amount, from_currency, to_currency):
    """Convert amount from one currency to another"""
    if from_currency == to_currency:
        return amount
    
    rate = get_exchange_rate(from_currency, to_currency)
    return amount * rate


@transaction.atomic
def create_multi_currency_payment(payment, original_currency, original_amount):
    """Create multi-currency payment record"""
    converted_amount = convert_currency(original_amount, original_currency, 'USD')
    rate = get_exchange_rate(original_currency, 'USD')
    
    return MultiCurrencyPayment.objects.create(
        payment=payment,
        original_currency=original_currency,
        original_amount=original_amount,
        converted_currency='USD',
        converted_amount=converted_amount,
        exchange_rate=rate
    )
