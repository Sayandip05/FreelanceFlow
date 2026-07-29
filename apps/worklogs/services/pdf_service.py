"""
PDF Service for generating weekly/progress reports and delivery proofs.

Uses WeasyPrint for HTML-to-PDF conversion, then uploads the resulting
PDF bytes to Azure Blob Storage (replaces legacy S3/boto3 upload).

WeasyPrint requires libgobject (part of GLib/GTK) — available in Docker/production.
On macOS without the system library the module still loads; PDF generation
will raise at call-time (not at import time).

Azure Upload:
    - Connection: AZURE_STORAGE_CONNECTION_STRING from settings
    - Container:  AZURE_CONTAINER_NAME (default: "media")
    - Blob naming:
        Progress reports:   reports/{contract_id}/report_{date}.pdf
        Delivery proofs:    proofs/{contract_id}/delivery_proof.pdf
    - Access: Private container, 7-day SAS URL returned to caller
"""
from django.conf import settings
from django.template.loader import render_to_string
from io import BytesIO
from apps.worklogs.models import WeeklyReport, DeliveryProof, WorkLog


# ─────────────────────────────────────────────────────────────────────────────
# Azure Blob Storage Upload
# ─────────────────────────────────────────────────────────────────────────────

def upload_to_azure_blob(pdf_bytes: bytes, blob_name: str) -> str:
    """
    Upload PDF bytes to Azure Blob Storage and return a SAS URL (7-day expiry).

    Falls back to a placeholder URL in local development when
    AZURE_STORAGE_CONNECTION_STRING is not configured.

    Args:
        pdf_bytes:  Raw PDF content
        blob_name:  Blob path within the container (e.g. "reports/42/report_2026-07-28.pdf")

    Returns:
        Publicly-accessible SAS URL valid for 7 days.
    """
    connection_string = getattr(settings, "AZURE_STORAGE_CONNECTION_STRING", None)
    container_name = getattr(settings, "AZURE_CONTAINER_NAME", "media")

    if not connection_string:
        # Local dev fallback — no Azure credentials needed
        return f"https://placeholder-azure-blob-url/{blob_name}"

    try:
        from azure.storage.blob import (
            BlobServiceClient,
            ContentSettings,
            generate_blob_sas,
            BlobSasPermissions,
        )
        from datetime import datetime, timedelta, timezone

        # Connect to storage account
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)

        # Upload PDF (overwrite existing blob with same name)
        blob_client.upload_blob(
            BytesIO(pdf_bytes),
            overwrite=True,
            content_settings=ContentSettings(content_type="application/pdf"),
        )

        # Generate SAS URL valid for 7 days
        expiry = datetime.now(timezone.utc) + timedelta(days=7)
        account_name = blob_service_client.account_name
        account_key = blob_service_client.credential.account_key

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry,
        )

        return (
            f"https://{account_name}.blob.core.windows.net"
            f"/{container_name}/{blob_name}?{sas_token}"
        )

    except Exception as exc:
        # Never crash a Celery task over a storage issue — log and fall back
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Azure Blob upload failed for %s: %s", blob_name, exc, exc_info=True)
        return f"https://placeholder-azure-blob-url/{blob_name}"


# ─────────────────────────────────────────────────────────────────────────────
# Progress Report PDF
# ─────────────────────────────────────────────────────────────────────────────

def generate_weekly_report_pdf(report_id: int) -> str:
    """
    Generate PDF for a progress report and upload to Azure Blob Storage.

    This function is called inside the `generate_pdf_task` Celery worker —
    it NEVER blocks the HTTP request lifecycle.

    Args:
        report_id: WeeklyReport (ProgressReport) ID

    Returns:
        Azure Blob SAS URL of the generated PDF (7-day expiry)
    """
    try:
        report = WeeklyReport.objects.select_related(
            "contract__bid__project__client",
            "contract__bid__freelancer",
        ).get(id=report_id)
    except WeeklyReport.DoesNotExist:
        raise ValueError(f"WeeklyReport {report_id} not found")

    # Get work logs for the covered period
    logs = WorkLog.objects.filter(
        contract=report.contract,
        date__range=[report.week_start, report.week_end],
    ).order_by("date")

    # Render HTML → PDF bytes
    html_string = render_to_string(
        "worklogs/weekly_report.html",
        {
            "report": report,
            "logs": logs,
            "project": report.contract.bid.project,
            "freelancer": report.contract.bid.freelancer,
            "client": report.contract.bid.project.client,
        },
    )

    from weasyprint import HTML
    pdf_bytes = HTML(string=html_string).write_pdf()

    # Upload to Azure Blob Storage
    blob_name = (
        f"reports/{report.contract.id}/report_{report.week_start}.pdf"
    )
    pdf_url = upload_to_azure_blob(pdf_bytes, blob_name)

    # Persist URL back to the report record
    report.pdf_url = pdf_url
    report.save(update_fields=["pdf_url"])

    return pdf_url


# ─────────────────────────────────────────────────────────────────────────────
# Delivery Proof PDF
# ─────────────────────────────────────────────────────────────────────────────

def generate_delivery_proof_pdf(proof_id: int) -> str:
    """
    Generate PDF for a delivery proof and upload to Azure Blob Storage.

    Args:
        proof_id: DeliveryProof ID

    Returns:
        Azure Blob SAS URL of the generated PDF (7-day expiry)
    """
    try:
        proof = DeliveryProof.objects.select_related(
            "contract__bid__project__client",
            "contract__bid__freelancer",
        ).get(id=proof_id)
    except DeliveryProof.DoesNotExist:
        raise ValueError(f"DeliveryProof {proof_id} not found")

    # Aggregate all logs and reports for this contract
    logs = WorkLog.objects.filter(contract=proof.contract).order_by("date")
    reports = WeeklyReport.objects.filter(contract=proof.contract).order_by("week_start")

    # Render HTML → PDF bytes
    html_string = render_to_string(
        "worklogs/delivery_proof.html",
        {
            "proof": proof,
            "logs": logs,
            "reports": reports,
            "project": proof.contract.bid.project,
            "freelancer": proof.contract.bid.freelancer,
            "client": proof.contract.bid.project.client,
        },
    )

    from weasyprint import HTML
    pdf_bytes = HTML(string=html_string).write_pdf()

    # Upload to Azure Blob Storage
    blob_name = f"proofs/{proof.contract.id}/delivery_proof.pdf"
    pdf_url = upload_to_azure_blob(pdf_bytes, blob_name)

    # Persist URL
    proof.pdf_url = pdf_url
    proof.save(update_fields=["pdf_url"])

    return pdf_url
