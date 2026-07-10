"""
Tests for apps.worklogs.services
Covers: create_worklog, update_worklog, delete_worklog, generate_delivery_proof
"""
from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase

from apps.bidding.models import Bid
from apps.projects.tests.factories import make_client, make_freelancer, make_project, make_bid, make_contract
from apps.worklogs.models import WorkLog, DeliveryProof
from apps.worklogs.services import create_worklog, update_worklog, delete_worklog, generate_delivery_proof
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError


def _make_contract():
    client = make_client()
    freelancer = make_freelancer()
    project = make_project(client)
    bid = make_bid(project, freelancer, status=Bid.Status.ACCEPTED)
    return make_contract(bid), freelancer, client


class CreateWorklogTests(TestCase):
    def setUp(self):
        self.contract, self.freelancer, self.client_user = _make_contract()

    @patch("apps.worklogs.services.notify_client_log_submitted.delay")
    def test_create_worklog_success(self, mock_notify):
        log = create_worklog(
            freelancer=self.freelancer,
            contract_id=self.contract.id,
            log_date=date.today(),
            description="Implemented user authentication system today.",
            hours_worked=8.0,
        )
        self.assertIsInstance(log, WorkLog)
        self.assertEqual(log.freelancer, self.freelancer)
        self.assertEqual(float(log.hours_worked), 8.0)

    def test_client_cannot_create_worklog(self):
        with self.assertRaises(PermissionDeniedError):
            create_worklog(
                freelancer=self.client_user,
                contract_id=self.contract.id,
                log_date=date.today(),
                description="Implemented user authentication system today.",
                hours_worked=8.0,
            )

    def test_cannot_log_for_nonexistent_contract(self):
        with self.assertRaises(NotFoundError):
            create_worklog(
                freelancer=self.freelancer,
                contract_id=99999,
                log_date=date.today(),
                description="Some work done today on the project.",
                hours_worked=8.0,
            )

    def test_cannot_log_to_other_freelancers_contract(self):
        other_freelancer = make_freelancer(email="other@test.com")
        with self.assertRaises(PermissionDeniedError):
            create_worklog(
                freelancer=other_freelancer,
                contract_id=self.contract.id,
                log_date=date.today(),
                description="Some work done today on the project.",
                hours_worked=8.0,
            )

    @patch("apps.worklogs.services.notify_client_log_submitted.delay")
    def test_cannot_log_same_day_twice(self, mock_notify):
        create_worklog(
            freelancer=self.freelancer,
            contract_id=self.contract.id,
            log_date=date.today(),
            description="First log for this day's work on project.",
            hours_worked=8.0,
        )
        with self.assertRaises(ValidationError):
            create_worklog(
                freelancer=self.freelancer,
                contract_id=self.contract.id,
                log_date=date.today(),
                description="Second attempt for the same day work.",
                hours_worked=4.0,
            )

    def test_invalid_hours_zero(self):
        with self.assertRaises(ValidationError):
            create_worklog(
                freelancer=self.freelancer,
                contract_id=self.contract.id,
                log_date=date.today(),
                description="Some work done today on the project here.",
                hours_worked=0,
            )

    def test_invalid_hours_over_24(self):
        with self.assertRaises(ValidationError):
            create_worklog(
                freelancer=self.freelancer,
                contract_id=self.contract.id,
                log_date=date.today(),
                description="Some work done today on the project here.",
                hours_worked=25,
            )

    def test_description_too_short(self):
        with self.assertRaises(ValidationError):
            create_worklog(
                freelancer=self.freelancer,
                contract_id=self.contract.id,
                log_date=date.today(),
                description="Short",
                hours_worked=8.0,
            )

    def test_inactive_contract_raises_error(self):
        self.contract.is_active = False
        self.contract.save()
        with self.assertRaises(ValidationError):
            create_worklog(
                freelancer=self.freelancer,
                contract_id=self.contract.id,
                log_date=date.today(),
                description="Some work done today on the project here.",
                hours_worked=8.0,
            )


class UpdateWorklogTests(TestCase):
    def setUp(self):
        self.contract, self.freelancer, self.client_user = _make_contract()
        self.log = WorkLog.objects.create(
            contract=self.contract,
            freelancer=self.freelancer,
            date=date.today(),
            description="Original description for today's work on the project.",
            hours_worked=8.0,
        )

    def test_update_worklog_description(self):
        updated = update_worklog(
            log=self.log,
            freelancer=self.freelancer,
            description="Updated description for today's work completed.",
        )
        self.assertEqual(updated.description, "Updated description for today's work completed.")

    def test_update_hours(self):
        updated = update_worklog(log=self.log, freelancer=self.freelancer, hours_worked=6.0)
        self.assertEqual(float(updated.hours_worked), 6.0)

    def test_other_freelancer_cannot_update(self):
        other = make_freelancer(email="other2@test.com")
        with self.assertRaises(PermissionDeniedError):
            update_worklog(log=self.log, freelancer=other, description="Trying to update someone else's log today.")

    def test_invalid_hours_on_update(self):
        with self.assertRaises(ValidationError):
            update_worklog(log=self.log, freelancer=self.freelancer, hours_worked=0)


class DeleteWorklogTests(TestCase):
    def setUp(self):
        self.contract, self.freelancer, self.client_user = _make_contract()
        self.log = WorkLog.objects.create(
            contract=self.contract,
            freelancer=self.freelancer,
            date=date.today(),
            description="Log to be deleted for today's project work.",
            hours_worked=8.0,
        )

    def test_delete_worklog_success(self):
        delete_worklog(self.log, self.freelancer)
        self.assertFalse(WorkLog.objects.filter(id=self.log.id).exists())

    def test_other_freelancer_cannot_delete(self):
        other = make_freelancer(email="other3@test.com")
        with self.assertRaises(PermissionDeniedError):
            delete_worklog(self.log, other)


class GenerateDeliveryProofTests(TestCase):
    def setUp(self):
        self.contract, self.freelancer, self.client_user = _make_contract()

    @patch("apps.worklogs.services.generate_proof_pdf_task.delay")
    def test_generate_proof_creates_record(self, mock_pdf):
        WorkLog.objects.create(
            contract=self.contract,
            freelancer=self.freelancer,
            date=date.today(),
            description="Work done on the project feature today.",
            hours_worked=8.0,
        )
        proof = generate_delivery_proof(self.contract.id)
        self.assertIsInstance(proof, DeliveryProof)
        self.assertEqual(proof.total_logs_count, 1)

    def test_generate_proof_for_nonexistent_contract(self):
        with self.assertRaises(NotFoundError):
            generate_delivery_proof(99999)
