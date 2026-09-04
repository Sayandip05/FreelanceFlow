from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class OtpRegistrationIntegrationTests(APITestCase):
    """
    Integration tests for user registration with 6-digit OTP verification.
    """

    def setUp(self):
        cache.clear()
        self.reg_url = reverse("register-otp-initiate")
        self.verify_url = reverse("register-otp-verify")
        self.resend_url = reverse("register-otp-resend")

        self.user_data = {
            "email": "testuser_otp@example.com",
            "password": "StrongPassword123!",
            "role": "FREELANCER",
            "first_name": "Test",
            "last_name": "User",
        }

    def tearDown(self):
        cache.clear()

    @patch("apps.users.services.otp_service.send_mail")
    def test_full_registration_flow_success(self, mock_send_mail):
        """Test complete registration flow: initiate -> email sent -> verify -> user created."""
        # 1. Initiate registration
        init_res = self.client.post(self.reg_url, self.user_data)
        self.assertEqual(init_res.status_code, status.HTTP_200_OK)
        self.assertIn("Verification OTP sent", init_res.data["message"])
        self.assertTrue(mock_send_mail.called)

        # 2. Verify user is NOT yet in the database
        self.assertFalse(User.objects.filter(email=self.user_data["email"]).exists())

        # 3. Retrieve OTP from cache
        reg_key = f"otp:reg:{self.user_data['email']}"
        cache_data = cache.get(reg_key)
        self.assertIsNotNone(cache_data)
        otp = cache_data["otp"]
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

        # 4. Verify OTP
        verify_res = self.client.post(self.verify_url, {
            "email": self.user_data["email"],
            "otp": otp,
        })
        self.assertEqual(verify_res.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", verify_res.data)
        self.assertIn("access", verify_res.data["tokens"])
        self.assertIn("refresh", verify_res.data["tokens"])

        # 5. Verify user is created in PostgreSQL with email verified
        user = User.objects.filter(email=self.user_data["email"]).first()
        self.assertIsNotNone(user)
        self.assertTrue(user.is_email_verified)
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.role, "FREELANCER")
        self.assertTrue(user.check_password("StrongPassword123!"))

        # 6. Verify cache was cleaned up
        self.assertIsNone(cache.get(reg_key))

    @patch("apps.users.services.otp_service.send_mail")
    def test_registration_cooldown_enforced(self, mock_send_mail):
        """Test that resending OTP before 30 seconds cooldown triggers 400 error."""
        # 1. Initiate first time
        init_res = self.client.post(self.reg_url, self.user_data)
        self.assertEqual(init_res.status_code, status.HTTP_200_OK)

        # 2. Try to resend immediately
        resend_res = self.client.post(self.resend_url, {"email": self.user_data["email"]})
        self.assertEqual(resend_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("wait", str(resend_res.data).lower())

    @patch("apps.users.services.otp_service.send_mail")
    def test_registration_wrong_otp_attempts(self, mock_send_mail):
        """Test that entering wrong OTP increments failure count and locks after 5 attempts."""
        # 1. Initiate
        self.client.post(self.reg_url, self.user_data)

        # 2. Enter wrong OTP 4 times
        for i in range(1, 5):
            res = self.client.post(self.verify_url, {
                "email": self.user_data["email"],
                "otp": "000000",
            })
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(f"{5 - i} attempt", str(res.data))

        # 3. 5th wrong attempt should lock out / invalidate OTP
        res5 = self.client.post(self.verify_url, {
            "email": self.user_data["email"],
            "otp": "000000",
        })
        self.assertEqual(res5.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. Attempting again should report expired/invalidated
        res6 = self.client.post(self.verify_url, {
            "email": self.user_data["email"],
            "otp": "000000",
        })
        self.assertEqual(res6.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.users.services.otp_service.send_mail")
    def test_cannot_register_existing_email(self, mock_send_mail):
        """Test that initiate fails if email already exists."""
        User.objects.create_user(
            email=self.user_data["email"],
            password="ExistingPassword123!",
            role="CLIENT"
        )
        res = self.client.post(self.reg_url, self.user_data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(res.data.get("field") == "email" or "email" in str(res.data))



class OtpPasswordResetIntegrationTests(APITestCase):
    """
    Integration tests for password reset with 6-digit OTP verification.
    """

    def setUp(self):
        cache.clear()
        self.init_url = reverse("password-reset-otp-initiate")
        self.verify_url = reverse("password-reset-otp-verify")
        self.resend_url = reverse("password-reset-otp-resend")

        self.user = User.objects.create_user(
            email="reset_test@example.com",
            password="OldPassword123!",
            first_name="Reset",
            last_name="Tester",
            role="CLIENT",
            is_email_verified=True,
        )

    def tearDown(self):
        cache.clear()

    @patch("apps.users.services.otp_service.send_mail")
    def test_full_password_reset_flow_success(self, mock_send_mail):
        """Test password reset: initiate -> verify with new password -> login works."""
        # 1. Initiate password reset
        init_res = self.client.post(self.init_url, {"email": self.user.email})
        self.assertEqual(init_res.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_send_mail.called)

        # 2. Get OTP from cache
        pwd_key = f"otp:pwd:{self.user.email}"
        cache_data = cache.get(pwd_key)
        self.assertIsNotNone(cache_data)
        otp = cache_data["otp"]
        self.assertEqual(len(otp), 6)

        # 3. Verify OTP and set new password
        verify_res = self.client.post(self.verify_url, {
            "email": self.user.email,
            "otp": otp,
            "new_password": "NewBrandPassword456!",
        })
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)

        # 4. Verify password was updated in DB
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("OldPassword123!"))
        self.assertTrue(self.user.check_password("NewBrandPassword456!"))

        # 5. Verify cache key was removed
        self.assertIsNone(cache.get(pwd_key))

    @patch("apps.users.services.otp_service.send_mail")
    def test_password_reset_nonexistent_email(self, mock_send_mail):
        """Test that initiating reset for non-existent email fails with 400."""
        res = self.client.post(self.init_url, {"email": "nobody@example.com"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(mock_send_mail.called)

    @patch("apps.users.services.otp_service.send_mail")
    def test_password_reset_cooldown(self, mock_send_mail):
        """Test resend password reset OTP cooldown."""
        self.client.post(self.init_url, {"email": self.user.email})
        resend_res = self.client.post(self.resend_url, {"email": self.user.email})
        self.assertEqual(resend_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("wait", str(resend_res.data).lower())
