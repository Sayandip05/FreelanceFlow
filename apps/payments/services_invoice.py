"""Invoice generation service."""
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
import os
from datetime import datetime

from .models import Payment
from apps.bidding.models import Contract
from core.exceptions import NotFoundError


def generate_invoice_pdf(payment_id: int) -> str:
    """
    Generate PDF invoice for a payment.
    
    Args:
        payment_id: Payment ID
    
    Returns:
        Path to generated PDF file
    """
    try:
        payment = Payment.objects.select_related(
            'contract__bid__project__client',
            'contract__bid__freelancer'
        ).get(id=payment_id)
    except Payment.DoesNotExist:
        raise NotFoundError("Payment not found.")
    
    contract = payment.contract
    project = contract.bid.project
    client = project.client
    freelancer = contract.bid.freelancer
    
    # Calculate platform cut
    from core.utils import calculate_platform_cut
    cut_info = calculate_platform_cut(
        payment.total_amount,
        settings.PLATFORM_CUT_PERCENTAGE
    )
    
    # Prepare invoice data
    invoice_data = {
        'invoice_number': f"INV-{payment.id:06d}",
        'invoice_date': payment.created_at.strftime('%Y-%m-%d'),
        'due_date': payment.created_at.strftime('%Y-%m-%d'),
        'payment': payment,
        'contract': contract,
        'project': project,
        'client': client,
        'freelancer': freelancer,
        'platform_cut': cut_info['cut_amount'],
        'freelancer_amount': cut_info['freelancer_amount'],
        'company_name': 'FreelanceFlow',
        'company_address': '123 Business St, City, Country',
        'company_email': settings.DEFAULT_FROM_EMAIL,
    }
    
    # Render HTML template
    html_string = render_to_string('invoices/invoice_template.html', invoice_data)
    
    # Generate PDF
    pdf_filename = f"invoice_{payment.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'invoices', pdf_filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    # Create PDF
    HTML(string=html_string).write_pdf(pdf_path)
    
    return pdf_path


def get_invoice_html(payment_id: int) -> str:
    """
    Get HTML invoice for preview.
    
    Args:
        payment_id: Payment ID
    
    Returns:
        HTML string
    """
    try:
        payment = Payment.objects.select_related(
            'contract__bid__project__client',
            'contract__bid__freelancer'
        ).get(id=payment_id)
    except Payment.DoesNotExist:
        raise NotFoundError("Payment not found.")
    
    contract = payment.contract
    project = contract.bid.project
    client = project.client
    freelancer = contract.bid.freelancer
    
    from core.utils import calculate_platform_cut
    cut_info = calculate_platform_cut(
        payment.total_amount,
        settings.PLATFORM_CUT_PERCENTAGE
    )
    
    invoice_data = {
        'invoice_number': f"INV-{payment.id:06d}",
        'invoice_date': payment.created_at.strftime('%Y-%m-%d'),
        'due_date': payment.created_at.strftime('%Y-%m-%d'),
        'payment': payment,
        'contract': contract,
        'project': project,
        'client': client,
        'freelancer': freelancer,
        'platform_cut': cut_info['cut_amount'],
        'freelancer_amount': cut_info['freelancer_amount'],
        'company_name': 'FreelanceFlow',
        'company_address': '123 Business St, City, Country',
        'company_email': settings.DEFAULT_FROM_EMAIL,
    }
    
    return render_to_string('invoices/invoice_template.html', invoice_data)
