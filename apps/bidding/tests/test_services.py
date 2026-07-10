"""
Tests for apps.bidding.services
Covers: submit_bid, accept_bid, reject_bid, withdraw_bid, complete_contract
"""
from unittest.mock import patch

from django.test import TestCase

from apps.bidding.models import Bid, Contract
from apps.bidding.services import (
    submit_bid,
    accept_bid,
    reject_bid,
    withdraw_bid,
    complete_contract,
)
from apps.projects.tests.factories import make_client, make_freelancer, make_project, make_bid, make_contract
from apps.projects.models import Project
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError


class SubmitBidTests(TestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user, budget=5000)

    def test_submit_bid_success(self):
        bid = submit_bid(
            freelancer=self.freelancer,
            project_id=self.project.id,
            amount=3000,
            cover_letter="This is a detailed cover letter with more than fifty chars.",
        )
        self.assertEqual(bid.freelancer, self.freelancer)
        self.assertEqual(bid.project, self.project)
        self.assertEqual(bid.status, Bid.Status.PENDING)

    def test_client_cannot_submit_bid(self):
        with self.assertRaises(PermissionDeniedError):
            submit_bid(
                freelancer=self.client_user,
                project_id=self.project.id,
                amount=3000,
                cover_letter="This is a detailed cover letter with more than fifty chars.",
            )

    def test_cannot_bid_on_nonexistent_project(self):
        with self.assertRaises(NotFoundError):
            submit_bid(
                freelancer=self.freelancer,
                project_id=99999,
                amount=3000,
                cover_letter="This is a detailed cover letter with more than fifty chars.",
            )

    def test_cannot_bid_on_non_open_project(self):
        project = make_project(self.client_user, status=Project.Status.IN_PROGRESS)
        with self.assertRaises(ValidationError):
            submit_bid(
                freelancer=self.freelancer,
                project_id=project.id,
                amount=3000,
                cover_letter="This is a detailed cover letter with more than fifty chars.",
            )

    def test_cannot_bid_twice_on_same_project(self):
        make_bid(self.project, self.freelancer)
        with self.assertRaises(ValidationError):
            submit_bid(
                freelancer=self.freelancer,
                project_id=self.project.id,
                amount=2000,
                cover_letter="This is a detailed cover letter with more than fifty chars.",
            )

    def test_bid_amount_cannot_be_zero(self):
        with self.assertRaises(ValidationError):
            submit_bid(
                freelancer=self.freelancer,
                project_id=self.project.id,
                amount=0,
                cover_letter="This is a detailed cover letter with more than fifty chars.",
            )

    def test_bid_amount_cannot_exceed_budget(self):
        with self.assertRaises(ValidationError):
            submit_bid(
                freelancer=self.freelancer,
                project_id=self.project.id,
                amount=99999,
                cover_letter="This is a detailed cover letter with more than fifty chars.",
            )

    def test_cover_letter_too_short(self):
        with self.assertRaises(ValidationError):
            submit_bid(
                freelancer=self.freelancer,
                project_id=self.project.id,
                amount=3000,
                cover_letter="Too short",
            )


class AcceptBidTests(TestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user)
        self.bid = make_bid(self.project, self.freelancer)

    @patch("apps.notifications.tasks.notify_freelancer_bid_accepted.delay")
    def test_accept_bid_creates_contract(self, mock_notify):
        contract = accept_bid(self.bid.id, self.client_user)
        self.assertIsInstance(contract, Contract)
        self.bid.refresh_from_db()
        self.assertEqual(self.bid.status, Bid.Status.ACCEPTED)

    @patch("apps.notifications.tasks.notify_freelancer_bid_accepted.delay")
    def test_accept_bid_rejects_other_bids(self, mock_notify):
        freelancer2 = make_freelancer(email="fl2@test.com")
        bid2 = make_bid(self.project, freelancer2, amount=2500)
        accept_bid(self.bid.id, self.client_user)
        bid2.refresh_from_db()
        self.assertEqual(bid2.status, Bid.Status.REJECTED)

    @patch("apps.notifications.tasks.notify_freelancer_bid_accepted.delay")
    def test_accept_bid_sets_project_in_progress(self, mock_notify):
        accept_bid(self.bid.id, self.client_user)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.IN_PROGRESS)

    def test_non_owner_cannot_accept_bid(self):
        other_client = make_client(email="other@test.com")
        with self.assertRaises(PermissionDeniedError):
            accept_bid(self.bid.id, other_client)

    def test_accept_nonexistent_bid_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            accept_bid(99999, self.client_user)

    @patch("apps.notifications.tasks.notify_freelancer_bid_accepted.delay")
    def test_cannot_accept_already_accepted_bid(self, mock_notify):
        accept_bid(self.bid.id, self.client_user)
        freelancer2 = make_freelancer(email="fl3@test.com")
        bid2 = make_bid(
            make_project(self.client_user, title="Another Project"),
            freelancer2,
        )
        # Try to double-accept the original bid (now ACCEPTED status)
        with self.assertRaises(ValidationError):
            accept_bid(self.bid.id, self.client_user)


class RejectBidTests(TestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user)
        self.bid = make_bid(self.project, self.freelancer)

    def test_reject_bid_success(self):
        bid = reject_bid(self.bid.id, self.client_user)
        self.assertEqual(bid.status, Bid.Status.REJECTED)

    def test_non_owner_cannot_reject(self):
        other_client = make_client(email="other2@test.com")
        with self.assertRaises(PermissionDeniedError):
            reject_bid(self.bid.id, other_client)

    def test_reject_nonexistent_bid(self):
        with self.assertRaises(NotFoundError):
            reject_bid(99999, self.client_user)

    def test_cannot_reject_non_pending_bid(self):
        self.bid.status = Bid.Status.REJECTED
        self.bid.save()
        with self.assertRaises(ValidationError):
            reject_bid(self.bid.id, self.client_user)


class WithdrawBidTests(TestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user)
        self.bid = make_bid(self.project, self.freelancer)

    def test_withdraw_bid_success(self):
        bid = withdraw_bid(self.bid.id, self.freelancer)
        self.assertEqual(bid.status, Bid.Status.WITHDRAWN)

    def test_other_freelancer_cannot_withdraw(self):
        other_fl = make_freelancer(email="fl4@test.com")
        with self.assertRaises(PermissionDeniedError):
            withdraw_bid(self.bid.id, other_fl)

    def test_cannot_withdraw_accepted_bid(self):
        self.bid.status = Bid.Status.ACCEPTED
        self.bid.save()
        with self.assertRaises(ValidationError):
            withdraw_bid(self.bid.id, self.freelancer)


class CompleteContractTests(TestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user)
        self.bid = make_bid(self.project, self.freelancer, status=Bid.Status.ACCEPTED)
        self.contract = make_contract(self.bid)

    def test_complete_contract(self):
        contract = complete_contract(self.contract.id)
        self.assertFalse(contract.is_active)
        self.assertIsNotNone(contract.end_date)

    def test_complete_nonexistent_contract(self):
        with self.assertRaises(NotFoundError):
            complete_contract(99999)
