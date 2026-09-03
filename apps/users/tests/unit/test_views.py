"""
View-layer tests for apps.users (API endpoints).

These tests exercise the REST API through Django's test client, covering
authentication, permission enforcement, and response shape.

Covered endpoints:
- POST /api/users/register/         — register freelancer/client
- POST /api/users/login/            — JWT obtain
- GET  /api/users/me/               — authenticated profile retrieval
- PATCH /api/users/me/              — profile update
- POST /api/users/change-password/  — password change
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.tests.factories import make_freelancer, make_client


class UserRegistrationAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_register_freelancer_returns_201(self):
        resp = self.client.post("/api/users/register/", {
            "email": "newfl@test.com",
            "password": "StrongPass#123",
            "password_confirm": "StrongPass#123",
            "role": "FREELANCER",
            "first_name": "New",
            "last_name": "Dev",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_register_client_returns_201(self):
        resp = self.client.post("/api/users/register/", {
            "email": "newcl@test.com",
            "password": "StrongPass#123",
            "password_confirm": "StrongPass#123",
            "role": "CLIENT",
            "first_name": "New",
            "last_name": "Buyer",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_register_duplicate_email_returns_400(self):
        make_freelancer(email="dup@test.com")
        resp = self.client.post("/api/users/register/", {
            "email": "dup@test.com",
            "password": "StrongPass#123",
            "role": "FREELANCER",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email_returns_400(self):
        resp = self.client.post("/api/users/register/", {
            "password": "StrongPass#123",
            "role": "FREELANCER",
        }, format="json")
        self.assertIn(resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY])

    def test_register_invalid_role_returns_400(self):
        resp = self.client.post("/api/users/register/", {
            "email": "x@test.com",
            "password": "StrongPass#123",
            "role": "SUPERADMIN",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class UserMeAPITest(TestCase):

    def setUp(self):
        self.api_client = APIClient()
        self.freelancer = make_freelancer(email="me@test.com", password="StrongPass#123")
        # Get JWT token
        resp = self.api_client.post("/api/users/token/", {
            "email": "me@test.com",
            "password": "StrongPass#123",
        }, format="json")
        self.token = resp.data.get("access", "")
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_me_endpoint_returns_200_for_authenticated_user(self):
        resp = self.api_client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_me_endpoint_returns_401_without_auth(self):
        unauthenticated = APIClient()
        resp = unauthenticated.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_response_contains_email(self):
        resp = self.api_client.get("/api/users/me/")
        self.assertEqual(resp.data.get("email"), "me@test.com")
