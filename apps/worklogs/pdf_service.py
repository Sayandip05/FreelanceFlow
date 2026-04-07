"""
PDF Service for generating weekly reports and delivery proofs.
Uses WeasyPrint for HTML to PDF conversion.
"""
import boto3
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from io import BytesIO

from .models import WeeklyReport, DeliveryProof, WorkLog


def generate_weekly_report_pdf(report_id: int) -> str:
    """
    Generate PDF for a weekly report and upload to S3.
    
    Args:
        report_id: WeeklyReport ID
    
    Returns:
        S3 URL of the generated PDF
    """
    try:
        report = WeeklyReport.objects.select_related(
            'contract__bid__project__client',
            'contract__bid__freelancer'
        ).get(id=report_id)
    except WeeklyReport.DoesNotExist:
        raise ValueError("Report not found")
    
    # Get logs for the week
    logs = WorkLog.objects.filter(
        contract=report.contract,
        date__range=[report.week_start, report.week_end]
    ).order_by('date')
    
    # Render HTML template
    html_string = render_to_string('worklogs/weekly_report.html', {
        'report': report,
        'logs': logs,
        'project': report.contract.bid.project,
        'freelancer': report.contract.bid.freelancer,
        'client': report.contract.bid.project.client,
    })
    
    # Generate PDF
    html = HTML(string=html_string)
    pdf_bytes = html.write_pdf()
    
    # Upload to S3
    s3_key = f"reports/{report.contract.id}/week_{report.week_start}.pdf"
    pdf_url = upload_to_s3(pdf_bytes, s3_key)
    
    # Update report
    report.pdf_url = pdf_url
    report.save()
    
    return pdf_url


def generate_delivery_proof_pdf(proof_id: int) -> str:
    """
    Generate PDF for delivery proof and upload to S3.
    
    Args:
        proof_id: DeliveryProof ID
    
    Returns:
        S3 URL of the generated PDF
    """
    try:
        proof = DeliveryProof.objects.select_related(
            'contract__bid__project__client',
            'contract__bid__freelancer'
        ).get(id=proof_id)
    except DeliveryProof.DoesNotExist:
        raise ValueError("Proof not found")
    
    # Get all logs and reports
    logs = WorkLog.objects.filter(
        contract=proof.contract
    ).order_by('date')
    
    reports = WeeklyReport.objects.filter(
        contract=proof.contract
    ).order_by('week_start')
    
    # Render HTML template
    html_string = render_to_string('worklogs/delivery_proof.html', {
        'proof': proof,
        'logs': logs,
        'reports': reports,
        'project': proof.contract.bid.project,
        'freelancer': proof.contract.bid.freelancer,
        'client': proof.contract.bid.project.client,
    })
    
    # Generate PDF
    html = HTML(string=html_string)
    pdf_bytes = html.write_pdf()
    
    # Upload to S3
    s3_key = f"proofs/{proof.contract.id}/delivery_proof.pdf"
    pdf_url = upload_to_s3(pdf_bytes, s3_key)
    
    # Update proof
    proof.pdf_url = pdf_url
    proof.save()
    
    return pdf_url


def upload_to_s3(pdf_bytes: bytes, s3_key: str) -> str:
    """
    Upload PDF bytes to S3 and return pre-signed URL.
    
    Args:
        pdf_bytes: PDF file bytes
        s3_key: S3 object key
    
    Returns:
        Pre-signed S3 URL
    """
    if not settings.AWS_ACCESS_KEY_ID:
        # Return placeholder if S3 not configured
        return f"https://placeholder-s3-url/{s3_key}"
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    
    # Upload
    s3.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=s3_key,
        Body=pdf_bytes,
        ContentType='application/pdf',
    )
    
    # Generate pre-signed URL (valid for 7 days)
    url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': s3_key,
        },
        ExpiresIn=604800,  # 7 days
    )
    
    return url
