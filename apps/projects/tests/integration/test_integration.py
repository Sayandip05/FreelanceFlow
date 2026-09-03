import uuid
from decimal import Decimal
from django.test import TestCase, tag
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User
from apps.projects.models import Project, ProjectSkill


@tag("integration", "projects")
class ProjectIntegrationFlowTest(TestCase):
    """
    End-to-end integration test for project lifecycle:
    Client creates project -> Lists projects -> Updates -> Permission checks.
    """

    def setUp(self):
        self.client = APIClient()
        self.client_user = User.objects.create_user(
            email=f"client_{uuid.uuid4().hex[:6]}@example.com",
            password="StrongPass@123",
            role="CLIENT",
            is_email_verified=True,
        )
        self.freelancer_user = User.objects.create_user(
            email=f"freelancer_{uuid.uuid4().hex[:6]}@example.com",
            password="StrongPass@123",
            role="FREELANCER",
            is_email_verified=True,
        )

    def test_project_full_lifecycle(self):
        # 1. Authenticate as Client
        self.client.force_authenticate(user=self.client_user)

        # 2. Client creates project
        create_url = reverse("project-list")
        payload = {
            "title": "Build Fullstack Freelance Platform",
            "short_description": "Comprehensive marketplace application.",
            "description": "Comprehensive marketplace application with payment escrows.",
            "budget": "1500.00",
            "approx_duration": "1-2 months",
            "skill_names": ["React", "Django"],
        }
        res = self.client.post(create_url, payload, format="json")
        self.assertIn(res.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        project_id = res.data.get("id")
        self.assertIsNotNone(project_id)

        # 3. List projects (should include newly created project)
        list_res = self.client.get(create_url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        results = list_res.data.get("results") if isinstance(list_res.data, dict) else list_res.data
        self.assertTrue(any(p["id"] == project_id for p in results))

        # 4. Detail view
        detail_url = reverse("project-detail", kwargs={"pk": project_id})
        detail_res = self.client.get(detail_url)
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data["title"], "Build Fullstack Freelance Platform")

        # 5. Freelancer should NOT be able to modify the project (Security Boundary)
        self.client.force_authenticate(user=self.freelancer_user)
        patch_res = self.client.patch(detail_url, {"title": "Hacked Title"}, format="json")
        self.assertIn(patch_res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

        # 6. Original Client updates project description
        self.client.force_authenticate(user=self.client_user)
        update_res = self.client.patch(detail_url, {"description": "Updated project requirements."}, format="json")
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)
        self.assertEqual(update_res.data["description"], "Updated project requirements.")
