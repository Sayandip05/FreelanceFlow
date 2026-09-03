import uuid
from django.test import TestCase, tag
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User


@tag("integration", "users")
class UserIntegrationFlowTest(TestCase):
    """
    End-to-end integration test for user lifecycle:
    Registration -> Profile setup -> Login -> Token Refresh.
    """

    def setUp(self):
        self.client = APIClient()
        self.freelancer_email = f"freelancer_{uuid.uuid4().hex[:6]}@example.com"
        self.client_email = f"client_{uuid.uuid4().hex[:6]}@example.com"
        self.password = "StrongPass@123"

    def test_freelancer_complete_lifecycle(self):
        # 1. Register as Freelancer
        register_url = reverse("register")
        payload = {
            "email": self.freelancer_email,
            "password": self.password,
            "role": "FREELANCER",
            "first_name": "Test",
            "last_name": "Freelancer",
        }
        res = self.client.post(register_url, payload, format="json")
        self.assertIn(res.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])

        user = User.objects.get(email=self.freelancer_email)
        self.assertEqual(user.role, "FREELANCER")
        user.is_email_verified = True
        user.is_active = True
        user.save()

        # 2. Login to obtain JWT tokens
        login_url = reverse("login")
        login_res = self.client.post(login_url, {"email": self.freelancer_email, "password": self.password}, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        tokens = login_res.data.get("tokens", {})
        access_token = tokens.get("access") or login_res.data.get("access")
        refresh_token = tokens.get("refresh") or login_res.data.get("refresh")
        self.assertIsNotNone(access_token)

        # 3. Authenticated requests using access token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 4. View Freelancer Profile
        profile_url = reverse("profile")
        me_res = self.client.get(profile_url)
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        self.assertEqual(me_res.data["email"], self.freelancer_email)

        # 5. Token refresh
        if refresh_token:
            self.client.credentials()  # Clear auth headers
            refresh_url = reverse("token-refresh")
            ref_res = self.client.post(refresh_url, {"refresh": refresh_token}, format="json")
            self.assertEqual(ref_res.status_code, status.HTTP_200_OK)
            new_access = ref_res.data.get("access")
            self.assertIsNotNone(new_access)

    def test_client_complete_lifecycle(self):
        # 1. Register as Client
        register_url = reverse("register")
        payload = {
            "email": self.client_email,
            "password": self.password,
            "role": "CLIENT",
            "first_name": "Test",
            "last_name": "Client",
        }
        res = self.client.post(register_url, payload, format="json")
        self.assertIn(res.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])

        user = User.objects.get(email=self.client_email)
        self.assertEqual(user.role, "CLIENT")
        user.is_email_verified = True
        user.is_active = True
        user.save()

        # 2. Login
        login_url = reverse("login")
        login_res = self.client.post(login_url, {"email": self.client_email, "password": self.password}, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        access_token = login_res.data.get("tokens", {}).get("access") or login_res.data.get("access")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 3. View client profile
        profile_url = reverse("profile")
        me_res = self.client.get(profile_url)
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        self.assertEqual(me_res.data["role"], "CLIENT")
