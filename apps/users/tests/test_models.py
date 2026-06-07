"""
Tests for apps.users models.

Coverage:
- User model: creation, __str__, full_name property, role choices
- Signal: FreelancerProfile / ClientProfile auto-created on user save
- FreelancerProfile: __str__, defaults
- ClientProfile: __str__, defaults
- Model-level uniqueness (email)
"""
from django.test import TestCase
from django.db import IntegrityError

from apps.users.models import User, FreelancerProfile, ClientProfile
from apps.users.tests.factories import make_freelancer, make_client


class UserModelTest(TestCase):

    def test_create_freelancer_creates_freelancer_profile(self):
        """Signal must auto-create FreelancerProfile when a FREELANCER user is saved."""
        user = make_freelancer()
        self.assertTrue(FreelancerProfile.objects.filter(user=user).exists())

    def test_create_client_creates_client_profile(self):
        """Signal must auto-create ClientProfile when a CLIENT user is saved."""
        user = make_client()
        self.assertTrue(ClientProfile.objects.filter(user=user).exists())

    def test_create_freelancer_does_not_create_client_profile(self):
        user = make_freelancer()
        self.assertFalse(ClientProfile.objects.filter(user=user).exists())

    def test_create_client_does_not_create_freelancer_profile(self):
        user = make_client()
        self.assertFalse(FreelancerProfile.objects.filter(user=user).exists())

    def test_user_str(self):
        user = make_freelancer(email="dev@example.com")
        self.assertEqual(str(user), "dev@example.com (FREELANCER)")

    def test_full_name_property_with_names(self):
        user = make_freelancer(first_name="Alice", last_name="Dev")
        self.assertEqual(user.full_name, "Alice Dev")

    def test_full_name_property_falls_back_to_email(self):
        user = make_freelancer(first_name="", last_name="", email="noname@test.com")
        self.assertEqual(user.full_name, "noname@test.com")

    def test_email_is_unique(self):
        make_freelancer(email="dup@test.com")
        with self.assertRaises(Exception):
            make_freelancer(email="dup@test.com")

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_username_is_none(self):
        """AbstractUser.username field must be removed."""
        user = make_freelancer()
        self.assertFalse(hasattr(user, "username") and user.username)

    def test_default_is_active_true(self):
        user = make_freelancer()
        self.assertTrue(user.is_active)

    def test_is_deactivated_defaults_false(self):
        user = make_freelancer()
        self.assertFalse(user.is_deactivated)
        self.assertIsNone(user.deactivated_at)

    def test_role_choices_are_correct(self):
        self.assertEqual(User.Roles.CLIENT, "CLIENT")
        self.assertEqual(User.Roles.FREELANCER, "FREELANCER")


class FreelancerProfileModelTest(TestCase):

    def setUp(self):
        self.user = make_freelancer(email="fl@test.com")
        self.profile = self.user.freelancer_profile

    def test_str(self):
        self.assertEqual(str(self.profile), "Freelancer: fl@test.com")

    def test_default_subscription_tier_is_free(self):
        self.assertEqual(self.profile.subscription_tier, FreelancerProfile.SubscriptionTier.FREE)

    def test_default_is_available_true(self):
        self.assertTrue(self.profile.is_available)

    def test_default_total_earned_zero(self):
        self.assertEqual(self.profile.total_earned, 0)

    def test_default_average_rating_zero(self):
        self.assertEqual(self.profile.average_rating, 0)

    def test_skills_default_empty_list(self):
        self.assertEqual(self.profile.skills, [])


class ClientProfileModelTest(TestCase):

    def setUp(self):
        self.user = make_client(email="cl@test.com")
        self.profile = self.user.client_profile

    def test_str(self):
        self.assertEqual(str(self.profile), "Client: cl@test.com")

    def test_default_total_spent_zero(self):
        self.assertEqual(self.profile.total_spent, 0)

    def test_default_average_rating_zero(self):
        self.assertEqual(self.profile.average_rating, 0)
