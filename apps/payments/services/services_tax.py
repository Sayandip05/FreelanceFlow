"""
Tax Document Services
Generates tax documents (1099, etc.) for freelancers
"""
from django.db import transaction
from decimal import Decimal
from .models_extended import TaxDocument


@transaction.atomic
def generate_tax_document(user, year, document_type='1099'):
    """Generate tax document for a user"""
    from .models import Payment
    
    # Calculate total earnings for the year
    earnings = Payment.objects.filter(
        contract__bid__freelancer=user,
        status='RELEASED',
        created_at__year=year
    ).aggregate(total=models.Sum('total_amount'))['total'] or Decimal('0')
    
    # Create tax document
    tax_doc = TaxDocument.objects.create(
        user=user,
        year=year,
        document_type=document_type,
        total_earnings=earnings
    )
    
    # Generate PDF (implement PDF generation logic)
    # tax_doc.pdf_url = generate_pdf(tax_doc)
    # tax_doc.save()
    
    return tax_doc


def get_tax_documents(user, year=None):
    """Get tax documents for a user"""
    queryset = TaxDocument.objects.filter(user=user)
    if year:
        queryset = queryset.filter(year=year)
    return queryset.order_by('-year')
