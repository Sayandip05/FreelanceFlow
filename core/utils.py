import uuid
from decimal import Decimal, ROUND_HALF_UP


def calculate_platform_cut(amount, percentage=10):
    """
    Calculate platform cut and freelancer amount from a payment.
    
    Args:
        amount: Decimal or float - the total payment amount
        percentage: int - platform cut percentage (default 10)
    
    Returns:
        dict with 'cut_amount', 'freelancer_amount', 'total_amount'
    """
    amount = Decimal(str(amount))
    percentage = Decimal(str(percentage))
    
    cut_amount = (amount * percentage / 100).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    freelancer_amount = amount - cut_amount
    
    return {
        'total_amount': amount,
        'cut_amount': cut_amount,
        'freelancer_amount': freelancer_amount,
        'cut_percentage': percentage,
    }


def generate_report_id():
    """
    Generate a unique report identifier.
    
    Returns:
        str: UUID-based unique identifier
    """
    return str(uuid.uuid4())


def format_currency(amount, currency="$"):
    """
    Format a decimal amount as currency string.
    
    Args:
        amount: Decimal or float
        currency: str - currency symbol (default '$')
    
    Returns:
        str: Formatted currency string (e.g., "$1,234.56")
    """
    amount = Decimal(str(amount))
    return f"{currency}{amount:,.2f}"


def truncate_text(text, max_length=100, suffix="..."):
    """
    Truncate text to a maximum length.
    
    Args:
        text: str - text to truncate
        max_length: int - maximum length
        suffix: str - suffix to add if truncated
    
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rstrip() + suffix
