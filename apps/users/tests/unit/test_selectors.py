"""
Tests for apps.users.selectors.

Coverage:
- get_user_by_email: found / not found
- get_freelancer_profile / get_client_profile: returns profile or None
- list_freelancers: no filter, skill filter, limit
- list_clients: returns queryset
"""
from django.test import TestCase
from apps.users.selectors import (
    get_user_by_email,
    get_freelancer_profile,
    get_client_profile,
    list_freelancers,
    list_clients,
)
from apps.users.tests.factories import make_freelancer, make_client
class GetUserByEmailTest(TestCase):

    def test_returns_user_if_found(self):
        user = make_freelancer(email="found@test.com")
        result = get_user_by_email("found@test.com")
        self.assertEqual(result, user)

    def test_returns_none_if_not_found(self):
        result = get_user_by_email("missing@test.com")
        self.assertIsNone(result)


class GetProfileSelectorsTest(TestCase):

    def test_get_freelancer_profile_returns_profile(self):
        freelancer = make_freelancer()
        profile = get_freelancer_profile(freelancer)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user, freelancer)

    def test_get_freelancer_profile_returns_none_for_client(self):
        client = make_client()
        result = get_freelancer_profile(client)
        self.assertIsNone(result)

    def test_get_client_profile_returns_profile(self):
        client = make_client()
        profile = get_client_profile(client)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user, client)

    def test_get_client_profile_returns_none_for_freelancer(self):
        freelancer = make_freelancer()
        result = get_client_profile(freelancer)
        self.assertIsNone(result)


class ListFreelancersTest(TestCase):

    def setUp(self):
        self.f1 = make_freelancer(email="f1@test.com")
        self.f2 = make_freelancer(email="f2@test.com")
        # Give f1 some skills
        self.f1.freelancer_profile.skills = ["Python", "Django"]
        self.f1.freelancer_profile.save()
        # Give f2 different skills
        self.f2.freelancer_profile.skills = ["React", "TypeScript"]
        self.f2.freelancer_profile.save()

    def test_returns_all_freelancers(self):
        result = list(list_freelancers())
        self.assertEqual(len(result), 2)

    def test_skill_filter_returns_matching_freelancers(self):
        result = list(list_freelancers(skills=["Python"]))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].user, self.f1)

    def test_skill_filter_no_match_returns_empty(self):
        result = list(list_freelancers(skills=["Java"]))
        self.assertEqual(len(result), 0)

    def test_limit_is_respected(self):
        result = list(list_freelancers(limit=1))
        self.assertEqual(len(result), 1)


class ListClientsTest(TestCase):

    def test_returns_all_clients(self):
        make_client(email="c1@test.com")
        make_client(email="c2@test.com")
        result = list(list_clients())
        self.assertEqual(len(result), 2)
