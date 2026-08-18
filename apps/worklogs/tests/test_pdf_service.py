from datetime import date
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.projects.tests.factories import make_client, make_freelancer, make_project, make_bid, make_contract
from apps.worklogs.models import WeeklyReport, DeliveryProof, WorkLog
from apps.worklogs.services.pdf_service import (
    upload_to_azure_blob,
    generate_weekly_report_pdf,
    generate_delivery_proof_pdf,
)

try:
    from weasyprint import HTML
    # Test if WeasyPrint system libraries are actually loadable and callable
    HTML(string="<p></p>").write_pdf()
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False


class PDFServiceTests(TestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user)
        self.bid = make_bid(self.project, self.freelancer)
        self.contract = make_contract(self.bid)

    def test_upload_to_azure_blob_local_fallback(self):
        pdf_bytes = b"%PDF-1.4 test content"
        blob_name = f"reports/{self.contract.id}/report_test.pdf"
        url = upload_to_azure_blob(pdf_bytes, blob_name)
        self.assertIn("report_test.pdf", url)

    @patch("apps.worklogs.services.pdf_service.upload_to_azure_blob")
    def test_generate_weekly_report_pdf(self, mock_upload):
        mock_upload.return_value = "https://azure.blob.core.windows.net/media/reports/1/report.pdf?sas=123"

        report = WeeklyReport.objects.create(
            contract=self.contract,
            week_start=date.today(),
            week_end=date.today(),
            ai_summary="Summary of work completed.",
        )

        if WEASYPRINT_AVAILABLE:
            with patch("weasyprint.HTML") as mock_html_cls:
                mock_html_instance = MagicMock()
                mock_html_instance.write_pdf.return_value = b"%PDF-1.4 mock pdf content"
                mock_html_cls.return_value = mock_html_instance

                pdf_url = generate_weekly_report_pdf(report.id)
        else:
            with patch("fpdf.FPDF") as mock_fpdf_cls:
                mock_fpdf_instance = MagicMock()
                mock_fpdf_instance.output.return_value = b"%PDF-1.4 mock pdf content"
                mock_fpdf_cls.return_value = mock_fpdf_instance

                pdf_url = generate_weekly_report_pdf(report.id)

        self.assertIsNotNone(pdf_url)
        self.assertIn("https://", pdf_url)
        report.refresh_from_db()
        self.assertEqual(report.pdf_url, pdf_url)

    @patch("apps.worklogs.services.pdf_service.upload_to_azure_blob")
    def test_generate_delivery_proof_pdf(self, mock_upload):
        mock_upload.return_value = "https://azure.blob.core.windows.net/media/proofs/1/proof.pdf?sas=123"

        proof = DeliveryProof.objects.create(
            contract=self.contract,
            total_hours=40.0,
            total_logs_count=5,
            total_deliverables=2,
            approved_deliverables=2,
            report_id="RPT-TEST-12345",
        )

        if WEASYPRINT_AVAILABLE:
            with patch("weasyprint.HTML") as mock_html_cls:
                mock_html_instance = MagicMock()
                mock_html_instance.write_pdf.return_value = b"%PDF-1.4 mock proof content"
                mock_html_cls.return_value = mock_html_instance

                pdf_url = generate_delivery_proof_pdf(proof.id)
        else:
            with patch("fpdf.FPDF") as mock_fpdf_cls:
                mock_fpdf_instance = MagicMock()
                mock_fpdf_instance.output.return_value = b"%PDF-1.4 mock proof content"
                mock_fpdf_cls.return_value = mock_fpdf_instance

                pdf_url = generate_delivery_proof_pdf(proof.id)

        self.assertIsNotNone(pdf_url)
        self.assertIn("https://", pdf_url)
        proof.refresh_from_db()
        self.assertEqual(proof.pdf_url, pdf_url)
