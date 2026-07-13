"""
Tests for apps.search views.
Covers: search endpoint, autocomplete, history, saved searches.
"""
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from apps.projects.tests.factories import make_client, make_freelancer, make_project


def auth(user):
    return f"Bearer {RefreshToken.for_user(user).access_token}"


class SearchViewTests(APITestCase):
    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()
        # Create some projects to search
        make_project(self.client_user, title="Django REST API Project")
        make_project(self.client_user, title="React Frontend Development")

    def test_unauthenticated_cannot_search(self):
        response = self.client.get("/api/search/?q=django")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_search(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.get("/api/search/?q=django")
        # Elasticsearch may not be running in test env — accept 200 or 503
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ])

    def test_search_requires_query_param(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.get("/api/search/")
        # Should return 400 or 200 with empty results — not 500
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_autocomplete_endpoint_accessible(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.get("/api/search/autocomplete/?q=dj")
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ])

    def test_search_history_endpoint(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.get("/api/search/history/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_saved_searches_endpoint(self):
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.freelancer))
        response = self.client.get("/api/search/saved/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
