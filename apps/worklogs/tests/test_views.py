"""
Tests for apps.worklogs views (WorkLogViewSet, WeeklyReportViewSet, DeliverableViewSet).
"""
from datetime import date, timedelta
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from apps.bidding.models import Bid
from apps.projects.tests.factories import make_client, make_freelancer, make_project, make_bid, make_contract
from apps.worklogs.models import WorkLog, WeeklyReport, Deliverable
def auth(user):
    return f"Bearer {RefreshToken.for_user(user).access_token}"


def _setup():
    client_user = make_client()
    freelancer = make_freelancer()
    project = make_project(client_user)
    bid = make_bid(project, freelancer, status=Bid.Status.ACCEPTED)
    contract = make_contract(bid)
    return client_user, freelancer, contract


class WorkLogViewTests(APITestCase):
    def setUp(self):
        self.client_user, self.freelancer, self.contract = _setup()

    @patch("apps.worklogs.services.notify_client_log_submitted.delay")
    def test_freelancer_can_create_worklog(self, mock_notify):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.post(
            f"/api/worklogs/logs/?contract={self.contract.id}",
            {
                "date": str(date.today()),
                "description": "Worked on user authentication system implementation.",
                "hours_worked": 8.0,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch("apps.worklogs.services.notify_client_log_submitted.delay")
    def test_client_can_list_worklogs(self, mock_notify):
        WorkLog.objects.create(
            contract=self.contract,
            freelancer=self.freelancer,
            date=date.today(),
            description="Work done on the project today.",
            hours_worked=8.0,
        )
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.client_user))
        response = self.client.get(f"/api/worklogs/logs/?contract={self.contract.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_access(self):
        response = self.client.get("/api/worklogs/logs/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("apps.worklogs.services.notify_client_log_submitted.delay")
    def test_create_worklog_missing_contract_param(self, mock_notify):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.post(
            "/api/worklogs/logs/",
            {"date": str(date.today()), "description": "Work done.", "hours_worked": 8},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class WeeklyReportViewTests(APITestCase):
    def setUp(self):
        self.client_user, self.freelancer, self.contract = _setup()
        week_start = date.today() - timedelta(days=7)
        self.report = WeeklyReport.objects.create(
            contract=self.contract,
            week_start=week_start,
            week_end=week_start + timedelta(days=6),
            ai_summary="Weekly AI report summary text.",
        )

    def test_client_can_list_reports(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.client_user))
        response = self.client.get(f"/api/worklogs/reports/?contract={self.contract.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_freelancer_can_list_own_reports(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.get(f"/api/worklogs/reports/?contract={self.contract.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DeliverableViewTests(APITestCase):
    def setUp(self):
        self.client_user, self.freelancer, self.contract = _setup()

    def test_freelancer_can_create_deliverable(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.post(
            f"/api/worklogs/deliverables/?contract={self.contract.id}",
            {
                "title": "User Auth Module",
                "description": "Completed the user authentication module with JWT.",
                "hours_logged": 12,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_client_can_list_deliverables(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.client_user))
        response = self.client.get(f"/api/worklogs/deliverables/?contract={self.contract.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_client_can_approve_deliverable(self):
        deliverable = Deliverable.objects.create(
            contract=self.contract,
            freelancer=self.freelancer,
            title="Feature X",
            description="Completed feature X implementation.",
            status=Deliverable.Status.SUBMITTED,
        )
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.client_user))
        response = self.client.post(
            f"/api/worklogs/deliverables/{deliverable.id}/approve/",
            {"action": "approve", "feedback": "Great work!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        deliverable.refresh_from_db()
        self.assertEqual(deliverable.status, Deliverable.Status.APPROVED)

    def test_freelancer_cannot_approve(self):
        deliverable = Deliverable.objects.create(
            contract=self.contract,
            freelancer=self.freelancer,
            title="Feature Y",
            description="Completed feature Y implementation.",
            status=Deliverable.Status.SUBMITTED,
        )
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.post(f"/api/worklogs/deliverables/{deliverable.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
