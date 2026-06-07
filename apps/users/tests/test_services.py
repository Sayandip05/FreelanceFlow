"""
Tests for apps.users.services.

Coverage:
- create_user: happy path, duplicate email, missing email, invalid role, weak password
- change_password: correct old password, wrong old password, weak new password
- update_profile: freelancer fields, client fields
- update_subscription_tier: valid tier, invalid tier, client calling it raises error
- toggle_freelancer_availability: on/off, client raises error
- deactivate_account / reactivate_account: full soft-delete lifecycle
"""
from unittest.mock import patch

from django.test import TestCase

from apps.users.models import User, FreelancerProfile
from apps.users.services import (
    create_user,
    change_password,
    update_profile,
    update_subscription_tier,
    toggle_freelancer_availability,
    deactivate_account,
    reactivate_account,
)
from apps.users.tests.factories import make_freelancer, make_client
from core.exceptions import ValidationError, BusinessError


class CreateUserServiceTest(TestCase):

    def test_create_freelancer_succeeds(self):
        user = create_user(
            email="new@test.com",
            password="StrongPass#123",
            role="FREELANCER",
            first_name="Test",
            last_name="User",
        )
        self.assertIsNotNone(user.pk)
        self.assertEqual(user.email, "new@test.com")
        self.assertEqual(user.role, User.Roles.FREELANCER)

    def test_create_client_succeeds(self):
        user = create_user(
            email="client@test.com",
            password="StrongPass#123",
            role="CLIENT",
        )
        self.assertEqual(user.role, User.Roles.CLIENT)

    def test_raises_on_empty_email(self):
        with self.assertRaises(ValidationError) as ctx:
            create_user(email="", password="StrongPass#123", role="FREELANCER")
        self.assertEqual(ctx.exception.field, "email")

    def test_raises_on_empty_password(self):
        with self.assertRaises(ValidationError) as ctx:
            create_user(email="x@test.com", password="", role="FREELANCER")
        self.assertEqual(ctx.exception.field, "password")

    def test_raises_on_invalid_role(self):
        with self.assertRaises(ValidationError) as ctx:
            create_user(email="x@test.com", password="StrongPass#123", role="ADMIN")
        self.assertEqual(ctx.exception.field, "role")

    def test_raises_on_duplicate_email(self):
        make_freelancer(email="dup@test.com")
        with self.assertRaises(ValidationError) as ctx:
            create_user(email="dup@test.com", password="StrongPass#123", role="FREELANCER")
        self.assertEqual(ctx.exception.field, "email")

    def test_raises_on_weak_password(self):
        """Django password validators must reject '123'."""
        with self.assertRaises(ValidationError) as ctx:
            create_user(email="x@test.com", password="123", role="FREELANCER")
        self.assertEqual(ctx.exception.field, "password")


class ChangePasswordServiceTest(TestCase):

    def setUp(self):
        self.user = make_freelancer(password="OldPass#123")

    def test_change_password_succeeds(self):
        updated = change_password(self.user, "OldPass#123", "NewPass#456")
        self.assertTrue(updated.check_password("NewPass#456"))

    def test_raises_on_wrong_old_password(self):
        with self.assertRaises(ValidationError) as ctx:
            change_password(self.user, "WrongOld#999", "NewPass#456")
        self.assertEqual(ctx.exception.field, "old_password")

    def test_raises_on_weak_new_password(self):
        with self.assertRaises(ValidationError) as ctx:
            change_password(self.user, "OldPass#123", "123")
        self.assertEqual(ctx.exception.field, "new_password")


class UpdateProfileServiceTest(TestCase):

    def test_update_freelancer_profile_fields(self):
        freelancer = make_freelancer()
        update_profile(freelancer, {
            "first_name": "Updated",
            "bio": "Expert Django developer",
            "skills": ["Python", "Django"],
            "hourly_rate": 75.0,
        })
        freelancer.refresh_from_db()
        profile = freelancer.freelancer_profile
        profile.refresh_from_db()

        self.assertEqual(freelancer.first_name, "Updated")
        self.assertEqual(profile.bio, "Expert Django developer")
        self.assertEqual(profile.skills, ["Python", "Django"])
        self.assertEqual(float(profile.hourly_rate), 75.0)

    def test_update_client_profile_fields(self):
        client = make_client()
        update_profile(client, {"first_name": "Bob", "company_name": "Acme Corp"})
        client.refresh_from_db()
        profile = client.client_profile
        profile.refresh_from_db()

        self.assertEqual(client.first_name, "Bob")
        self.assertEqual(profile.company_name, "Acme Corp")

    def test_update_ignores_unknown_user_fields(self):
        """Fields not in allowed_user_fields should be silently ignored."""
        freelancer = make_freelancer()
        # Should not raise an error
        update_profile(freelancer, {"email": "hacker@test.com"})
        freelancer.refresh_from_db()
        # email should NOT change
        self.assertNotEqual(freelancer.email, "hacker@test.com")


class UpdateSubscriptionTierServiceTest(TestCase):

    def test_upgrade_freelancer_to_pro(self):
        freelancer = make_freelancer()
        profile = update_subscription_tier(freelancer, FreelancerProfile.SubscriptionTier.PRO)
        self.assertEqual(profile.subscription_tier, "PRO")

    def test_downgrade_freelancer_to_free(self):
        freelancer = make_freelancer()
        update_subscription_tier(freelancer, "PRO")
        profile = update_subscription_tier(freelancer, FreelancerProfile.SubscriptionTier.FREE)
        self.assertEqual(profile.subscription_tier, "FREE")

    def test_raises_if_caller_is_client(self):
        client = make_client()
        with self.assertRaises(BusinessError):
            update_subscription_tier(client, "PRO")

    def test_raises_on_invalid_tier(self):
        freelancer = make_freelancer()
        with self.assertRaises(ValidationError) as ctx:
            update_subscription_tier(freelancer, "ENTERPRISE")
        self.assertEqual(ctx.exception.field, "tier")


class ToggleAvailabilityServiceTest(TestCase):

    def test_set_unavailable(self):
        freelancer = make_freelancer()
        profile = toggle_freelancer_availability(freelancer, False)
        self.assertFalse(profile.is_available)

    def test_set_available_again(self):
        freelancer = make_freelancer()
        toggle_freelancer_availability(freelancer, False)
        profile = toggle_freelancer_availability(freelancer, True)
        self.assertTrue(profile.is_available)

    def test_client_cannot_toggle_availability(self):
        client = make_client()
        with self.assertRaises(BusinessError):
            toggle_freelancer_availability(client, True)


class DeactivateAccountServiceTest(TestCase):

    def test_deactivate_sets_flags(self):
        user = make_freelancer(password="Pass#123")
        with patch("apps.users.services.send_mail"):
            deactivated = deactivate_account(user, "Pass#123")
        self.assertTrue(deactivated.is_deactivated)
        self.assertFalse(deactivated.is_active)
        self.assertIsNotNone(deactivated.deactivated_at)

    def test_deactivate_raises_on_wrong_password(self):
        user = make_freelancer(password="Pass#123")
        with self.assertRaises(ValidationError) as ctx:
            deactivate_account(user, "WrongPass")
        self.assertEqual(ctx.exception.field, "password")

    def test_deactivate_raises_if_already_deactivated(self):
        user = make_freelancer(password="Pass#123")
        with patch("apps.users.services.send_mail"):
            deactivate_account(user, "Pass#123")
        with self.assertRaises(ValidationError):
            deactivate_account(user, "Pass#123")

    def test_reactivate_restores_flags(self):
        user = make_freelancer(password="Pass#123")
        with patch("apps.users.services.send_mail"):
            deactivate_account(user, "Pass#123")
        reactivated = reactivate_account(user)
        self.assertFalse(reactivated.is_deactivated)
        self.assertTrue(reactivated.is_active)
        self.assertIsNone(reactivated.deactivated_at)

    def test_reactivate_raises_if_not_deactivated(self):
        user = make_freelancer()
        with self.assertRaises(ValidationError):
            reactivate_account(user)
