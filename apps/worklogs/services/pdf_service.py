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
from apps.worklogs.models import WeeklyReport, DeliveryProof, WorkLog, Deliverable


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

    from django.utils import timezone
    pdf_bytes = None
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_string).write_pdf()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("WeasyPrint error, falling back to fpdf2: %s", e)
        try:
            from fpdf import FPDF
            
            def clean_pdf_text(text) -> str:
                if not text:
                    return ""
                text_str = str(text)
                replacements = {
                    "\u2011": "-",  # Non-breaking hyphen
                    "\u2013": "-",  # En dash
                    "\u2014": "--", # Em dash
                    "\u2018": "'",  # Smart left single quote
                    "\u2019": "'",  # Smart right single quote
                    "\u201c": '"',  # Smart left double quote
                    "\u201d": '"',  # Smart right double quote
                    "\u2022": "*",  # Bullet point
                    "\u2026": "...",# Ellipsis
                    "\u2027": "-",  # Hyphenation point
                    "\u2010": "-",  # Hyphen
                }
                for k, v in replacements.items():
                    text_str = text_str.replace(k, v)
                return text_str.encode("latin-1", errors="replace").decode("latin-1")
            
            class ReportPDF(FPDF):
                def header(self):
                    self.set_font("Helvetica", "B", 14)
                    self.set_text_color(79, 70, 229)  # Indigo
                    self.cell(0, 8, "FREELANCEFLOW PROGRESS REPORT", border=0, ln=1, align="L")
                    self.set_font("Helvetica", "I", 9)
                    self.set_text_color(100, 116, 139)  # Slate
                    self.cell(0, 5, "Verified Contract Progress & Delivery Summary", border=0, ln=1, align="L")
                    self.set_draw_color(226, 232, 240)
                    self.set_line_width(0.5)
                    self.line(15, 26, 195, 26)
                    self.ln(6)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Helvetica", "I", 8)
                    self.set_text_color(148, 163, 184)  # Light grey
                    self.cell(0, 10, f"Compiled securely by FreelanceFlow AI - Page {self.page_no()}", border=0, align="C")


            pdf = ReportPDF()
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.set_margins(15, 15, 15)
            pdf.add_page()
            
            project = report.contract.bid.project
            freelancer = report.contract.bid.freelancer
            client = project.client

            # Metadata Info Card
            pdf.set_fill_color(248, 250, 252)
            pdf.set_draw_color(226, 232, 240)
            pdf.set_line_width(0.3)
            
            # Card Top Row: Project Title
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(32, 7, "Project Title:", border="LT", ln=0, fill=True)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(148, 7, clean_pdf_text(project.title), border="TR", ln=1, fill=True)

            # Card Middle Row: Client & Freelancer
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(32, 6, "Client:", border="L", ln=0, fill=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(58, 6, clean_pdf_text(client.get_full_name() or client.email), border=0, ln=0, fill=True)
            
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(32, 6, "Freelancer:", border=0, ln=0, fill=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(58, 6, clean_pdf_text(freelancer.get_full_name() or freelancer.email), border="R", ln=1, fill=True)

            # Card Bottom Row: Period & Total Hours
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(32, 6, "Billing Period:", border="LB", ln=0, fill=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(58, 6, f"{report.week_start} to {report.week_end}", border="B", ln=0, fill=True)
            
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(32, 6, "Hours Billed:", border="B", ln=0, fill=True)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(79, 70, 229)
            pdf.cell(58, 6, f"{report.total_hours} hrs", border="RB", ln=1, fill=True)

            pdf.ln(6)

            # Section 1: Executive / AI Progress Summary
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(67, 56, 202)  # Darker indigo
            pdf.cell(0, 7, "1. Executive Progress Summary", ln=1)
            pdf.set_draw_color(226, 232, 240)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)

            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(30, 41, 59)
            
            # Clean up markdown headers/bullets in summary
            summary_raw = report.ai_summary or ""
            for line in summary_raw.splitlines():
                line = line.strip()
                if not line:
                    pdf.ln(2)
                    continue
                if line.startswith("## ") or line.startswith("### "):
                    pdf.ln(2)
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.set_text_color(79, 70, 229)
                    pdf.cell(0, 6, clean_pdf_text(line.lstrip("#").strip()), ln=1)
                    pdf.set_font("Helvetica", "", 9.5)
                    pdf.set_text_color(30, 41, 59)
                elif line.startswith("- ") or line.startswith("* "):
                    pdf.cell(5, 5, "-", ln=0, align="R")
                    pdf.multi_cell(175, 5, clean_pdf_text(line[2:].strip()))
                    pdf.ln(1)

                else:
                    pdf.multi_cell(180, 5.5, clean_pdf_text(line))
                    pdf.ln(1)

            pdf.ln(5)

            # Section 2: Logged Daily Work Details
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(67, 56, 202)
            pdf.cell(0, 7, "2. Logged Daily Work & Milestone Contributions", ln=1)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)

            if not logs.exists():
                pdf.set_font("Helvetica", "I", 9.5)
                pdf.set_text_color(100, 116, 139)
                pdf.cell(0, 6, "No individual daily logs recorded for this period.", ln=1)
            else:
                for log in logs:
                    pdf.set_font("Helvetica", "B", 9.5)
                    pdf.set_text_color(15, 23, 42)
                    pdf.cell(30, 6, f"{log.date}:", ln=0)
                    pdf.set_font("Helvetica", "B", 9.5)
                    pdf.set_text_color(79, 70, 229)
                    pdf.cell(25, 6, f"[{log.hours_worked} hrs]", ln=0)
                    pdf.set_font("Helvetica", "", 9.5)
                    pdf.set_text_color(51, 65, 85)
                    
                    desc = clean_pdf_text(log.description or "General development and milestone tasks.")
                    # Wrap description cleanly across the remaining width
                    pdf.multi_cell(125, 5.5, desc)
                    pdf.ln(2)

            pdf_bytes = bytes(pdf.output())
        except Exception as e_fallback:
            import logging
            logging.getLogger(__name__).exception("fpdf2 fallback generation failed: %s", e_fallback)
            pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"


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
        "worklogs/deliverable.html",
        {
            "proof": proof,
            "logs": logs,
            "reports": reports,
            "project": proof.contract.bid.project,
            "freelancer": proof.contract.bid.freelancer,
            "client": proof.contract.bid.project.client,
        },
    )

    from django.utils import timezone
    pdf_bytes = None
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_string).write_pdf()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("WeasyPrint error, falling back to fpdf2: %s", e)
        try:
            from fpdf import FPDF
            
            def clean_pdf_text(text) -> str:
                if not text:
                    return ""
                text_str = str(text)
                replacements = {
                    "\u2011": "-",  # Non-breaking hyphen
                    "\u2013": "-",  # En dash
                    "\u2014": "--", # Em dash
                    "\u2018": "'",  # Smart left single quote
                    "\u2019": "'",  # Smart right single quote
                    "\u201c": '"',  # Smart left double quote
                    "\u201d": '"',  # Smart right double quote
                    "\u2022": "*",  # Bullet point
                    "\u2026": "...",# Ellipsis
                    "\u2027": "-",  # Hyphenation point
                    "\u2010": "-",  # Hyphen
                }
                for k, v in replacements.items():
                    text_str = text_str.replace(k, v)
                return text_str.encode("latin-1", errors="replace").decode("latin-1")
            
            class ProofPDF(FPDF):
                def header(self):
                    self.set_font("Helvetica", "B", 14)
                    self.set_text_color(79, 70, 229)  # Indigo
                    self.cell(0, 8, "FREELANCEFLOW VERIFIED DELIVERY PROOF", border=0, ln=1, align="L")
                    self.set_font("Helvetica", "I", 9)
                    self.set_text_color(100, 116, 139)  # Slate
                    self.cell(0, 5, "Official Project Completion & Final Asset Transfer Document", border=0, ln=1, align="L")
                    self.set_draw_color(226, 232, 240)
                    self.set_line_width(0.5)
                    self.line(15, 26, 195, 26)
                    self.ln(6)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Helvetica", "I", 8)
                    self.set_text_color(148, 163, 184)  # Light grey
                    self.cell(0, 10, f"Compiled securely by FreelanceFlow - Page {self.page_no()}", border=0, align="C")


            pdf = ProofPDF()
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.set_margins(15, 15, 15)
            pdf.add_page()

            project = proof.contract.bid.project
            freelancer = proof.contract.bid.freelancer
            client = project.client

            # Metadata Info Card
            pdf.set_fill_color(248, 250, 252)
            pdf.set_draw_color(226, 232, 240)
            pdf.set_line_width(0.3)

            # Card Top Row: Project Title
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(32, 7, "Project Title:", border="LT", ln=0, fill=True)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(148, 7, clean_pdf_text(project.title), border="TR", ln=1, fill=True)

            # Card Middle Row: Client & Freelancer
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(32, 6, "Client:", border="L", ln=0, fill=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(58, 6, clean_pdf_text(client.get_full_name() or client.email), border=0, ln=0, fill=True)

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(32, 6, "Freelancer:", border=0, ln=0, fill=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(58, 6, clean_pdf_text(freelancer.get_full_name() or freelancer.email), border="R", ln=1, fill=True)

            # Card Bottom Row: Contract ID & Status
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(32, 6, "Contract ID:", border="LB", ln=0, fill=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(58, 6, f"Contract #{proof.contract.id}", border="B", ln=0, fill=True)

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(32, 6, "Status:", border="B", ln=0, fill=True)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(16, 185, 129)  # Emerald green
            pdf.cell(58, 6, "Completed & Approved", border="RB", ln=1, fill=True)

            pdf.ln(6)

            # Section 1: Verification Details
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(67, 56, 202)
            pdf.cell(0, 7, "1. Final Delivery & Verification Details", ln=1)
            pdf.set_draw_color(226, 232, 240)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)

            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(180, 5.5, f"This document certifies that all milestones and agreed project deliverables for '{clean_pdf_text(project.title)}' under Contract #{proof.contract.id} have been completed, reviewed, and approved for final asset handover.")
            pdf.ln(5)

            # Section 2: Historical Work Logs
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(67, 56, 202)
            pdf.cell(0, 7, "2. Summary of Logged Contract Hours", ln=1)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)

            if not logs.exists():
                pdf.set_font("Helvetica", "I", 9.5)
                pdf.set_text_color(100, 116, 139)
                pdf.cell(0, 6, "No individual daily logs recorded for this contract.", ln=1)
            else:
                for log in logs:
                    pdf.set_font("Helvetica", "B", 9.5)
                    pdf.set_text_color(15, 23, 42)
                    pdf.cell(30, 6, f"{log.date}:", ln=0)
                    pdf.set_font("Helvetica", "B", 9.5)
                    pdf.set_text_color(79, 70, 229)
                    pdf.cell(25, 6, f"[{log.hours_worked} hrs]", ln=0)
                    pdf.set_font("Helvetica", "", 9.5)
                    pdf.set_text_color(51, 65, 85)
                    
                    desc = clean_pdf_text(log.description or "General development milestone.")
                    pdf.multi_cell(125, 5.5, desc)
                    pdf.ln(2)

            pdf_bytes = bytes(pdf.output())
        except Exception as e_fallback:
            import logging
            logging.getLogger(__name__).exception("fpdf2 fallback generation failed: %s", e_fallback)
            pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"


    # Upload to Azure Blob Storage
    blob_name = f"proofs/{proof.contract.id}/delivery_proof.pdf"
    pdf_url = upload_to_azure_blob(pdf_bytes, blob_name)

    # Persist URL
    proof.pdf_url = pdf_url
    proof.save(update_fields=["pdf_url"])

    return pdf_url
