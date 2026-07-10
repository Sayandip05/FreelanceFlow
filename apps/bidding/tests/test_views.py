"""
Tests for apps.bidding views (BidViewSet, ContractViewSet).
Covers: list, create, accept, reject, withdraw endpoints.
"""
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.bidding.models import Bid, Contract
from apps.projects.tests.factories import (
    make_client,
    make_freelancer,
    make_project,
    make_bid,
    make_contract,
)
from apps.projects.models import Project


def auth_header(user):
    token = RefreshToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token.access_token}"}


class BidListCreateViewTests(APITestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user)

    def test_freelancer_can_list_own_bids(self):
        make_bid(self.project, self.freelancer)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.freelancer).access_token}")
        response = self.client.get("/api/bids/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_freelancer_can_submit_bid(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.freelancer).access_token}")
        response = self.client.post("/api/bids/", {
            "project": self.project.id,
            "amount": 3000,
            "cover_letter": "This is a detailed cover letter with more than fifty characters here.",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_client_cannot_submit_bid(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.client_user).access_token}")
        response = self.client.post("/api/bids/", {
            "project": self.project.id,
            "amount": 3000,
            "cover_letter": "This is a detailed cover letter with more than fifty characters here.",
        })
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_unauthenticated_cannot_access_bids(self):
        response = self.client.get("/api/bids/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BidAcceptRejectViewTests(APITestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user)
        self.bid = make_bid(self.project, self.freelancer)

    @patch("apps.notifications.tasks.notify_freelancer_bid_accepted.delay")
    def test_client_can_accept_bid(self, mock_notify):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.client_user).access_token}")
        response = self.client.post(f"/api/bids/{self.bid.id}/accept/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bid.refresh_from_db()
        self.assertEqual(self.bid.status, Bid.Status.ACCEPTED)

    def test_client_can_reject_bid(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.client_user).access_token}")
        response = self.client.post(f"/api/bids/{self.bid.id}/reject/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bid.refresh_from_db()
        self.assertEqual(self.bid.status, Bid.Status.REJECTED)

    def test_freelancer_can_withdraw_own_bid(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.freelancer).access_token}")
        response = self.client.delete(f"/api/bids/{self.bid.id}/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])


class ContractViewTests(APITestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        self.project = make_project(self.client_user)
        self.bid = make_bid(self.project, self.freelancer, status=Bid.Status.ACCEPTED)
        self.contract = make_contract(self.bid)

    def test_freelancer_can_list_contracts(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.freelancer).access_token}")
        response = self.client.get("/api/contracts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_client_can_list_contracts(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.client_user).access_token}")
        response = self.client.get("/api/contracts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contract_detail_accessible_to_participant(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.freelancer).access_token}")
        response = self.client.get(f"/api/contracts/{self.contract.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
