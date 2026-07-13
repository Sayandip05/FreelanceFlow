"""
Tests for apps.worklogs.models
Covers: WorkLog, WeeklyReport, Deliverable, DeliveryProof model properties.
"""
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase

from apps.bidding.models import Bid, Contract
from apps.projects.tests.factories import make_client, make_freelancer, make_project, make_bid, make_contract
from apps.worklogs.models import WorkLog, WeeklyReport, Deliverable, DeliveryProof
def make_worklog(contract, freelancer, log_date=None, hours=8.0, description="Working on the feature implementation today."):
    return WorkLog.objects.create(
        contract=contract,
        freelancer=freelancer,
        date=log_date or date.today(),
        description=description,
        hours_worked=hours,
    )


class WorkLogModelTests(TestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user)
        self.bid = make_bid(self.project, self.freelancer, status=Bid.Status.ACCEPTED)
        self.contract = make_contract(self.bid)

    def test_create_worklog(self):
        log = make_worklog(self.contract, self.freelancer)
        self.assertEqual(log.freelancer, self.freelancer)
        self.assertEqual(log.contract, self.contract)
        self.assertEqual(log.status, WorkLog.Status.DRAFT)

    def test_is_approved_property_false_by_default(self):
        log = make_worklog(self.contract, self.freelancer)
        self.assertFalse(log.is_approved)

    def test_is_approved_property_true_when_approved(self):
        log = make_worklog(self.contract, self.freelancer)
        log.status = WorkLog.Status.APPROVED
        log.save()
        self.assertTrue(log.is_approved)

    def test_is_pending_property(self):
        log = make_worklog(self.contract, self.freelancer)
        log.status = WorkLog.Status.PENDING_APPROVAL
        log.save()
        self.assertTrue(log.is_pending)

    def test_unique_per_contract_per_day(self):
        from django.db import IntegrityError
        make_worklog(self.contract, self.freelancer, log_date=date.today())
        with self.assertRaises(IntegrityError):
            make_worklog(self.contract, self.freelancer, log_date=date.today())

    def test_str_representation(self):
        log = make_worklog(self.contract, self.freelancer)
        self.assertIn(self.project.title, str(log))


class WeeklyReportModelTests(TestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user)
        self.bid = make_bid(self.project, self.freelancer, status=Bid.Status.ACCEPTED)
        self.contract = make_contract(self.bid)

    def test_create_weekly_report(self):
        week_start = date.today() - timedelta(days=7)
        report = WeeklyReport.objects.create(
            contract=self.contract,
            week_start=week_start,
            week_end=week_start + timedelta(days=6),
            ai_summary="Summary of the week's work.",
        )
        self.assertEqual(report.contract, self.contract)

    def test_total_hours_property(self):
        week_start = date.today() - timedelta(days=7)
        report = WeeklyReport.objects.create(
            contract=self.contract,
            week_start=week_start,
            week_end=week_start + timedelta(days=6),
            ai_summary="Summary.",
        )
        make_worklog(self.contract, self.freelancer, log_date=week_start, hours=6.0)
        make_worklog(self.contract, self.freelancer, log_date=week_start + timedelta(days=1), hours=4.0)
        self.assertEqual(report.total_hours, Decimal("10.0"))

    def test_total_hours_zero_when_no_logs(self):
        week_start = date.today() - timedelta(days=7)
        report = WeeklyReport.objects.create(
            contract=self.contract,
            week_start=week_start,
            week_end=week_start + timedelta(days=6),
            ai_summary="Summary.",
        )
        self.assertEqual(report.total_hours, 0)


class DeliverableModelTests(TestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user)
        self.bid = make_bid(self.project, self.freelancer, status=Bid.Status.ACCEPTED)
        self.contract = make_contract(self.bid)

    def test_create_deliverable_draft(self):
        d = Deliverable.objects.create(
            contract=self.contract,
            freelancer=self.freelancer,
            title="API Integration",
            description="Completed the payment gateway integration.",
        )
        self.assertEqual(d.status, Deliverable.Status.DRAFT)

    def test_str_representation(self):
        d = Deliverable.objects.create(
            contract=self.contract,
            freelancer=self.freelancer,
            title="UI Components",
            description="Built all UI components.",
        )
        self.assertIn("UI Components", str(d))
