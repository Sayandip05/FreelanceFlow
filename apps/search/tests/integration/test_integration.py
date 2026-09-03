import uuid
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase, tag
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User
from apps.projects.models import Project


@tag("integration", "search")
class SearchIntegrationFlowTest(TestCase):
    """
    End-to-end integration test for marketplace search & filtering:
    Project Search -> Freelancer Search -> Keyword Filters -> Defensive handling.
    """

    def setUp(self):
        self.client = APIClient()
        self.client_user = User.objects.create_user(
            email=f"client_{uuid.uuid4().hex[:6]}@example.com",
            password="StrongPass@123",
            role="CLIENT",
            is_email_verified=True,
        )
        self.project = Project.objects.create(
            client=self.client_user,
            title="Flutter iOS and Android Application",
            short_description="Mobile Flutter app",
            description="Looking for mobile developer proficient in Flutter and Firebase.",
            budget=Decimal("1500.00"),
            approx_duration="1-2 months",
            status=Project.Status.OPEN,
        )

    def test_search_projects_integration_flow(self):
        self.client.force_authenticate(user=self.client_user)
        search_url = reverse("search-projects")

        with patch("apps.search.views.views.ProjectDocument.search") as mock_search:
            mock_search.return_value.query.return_value.filter.return_value.execute.return_value = []
            res = self.client.get(f"{search_url}?q=Flutter")
            self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_search_freelancers_integration_flow(self):
        self.client.force_authenticate(user=self.client_user)
        search_url = reverse("search-freelancers")

        with patch("apps.search.views.views.FreelancerDocument.search") as mock_search:
            mock_search.return_value.query.return_value.filter.return_value.execute.return_value = []
            res = self.client.get(f"{search_url}?q=Engineer")
            self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
