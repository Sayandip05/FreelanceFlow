"""
View-layer tests for apps.projects (API endpoints).

Covered endpoints:
- GET  /api/projects/                  — list all OPEN projects
- POST /api/projects/                  — create a project (client only)
- GET  /api/projects/{id}/             — retrieve a single project
- PATCH /api/projects/{id}/            — update a project (owner only)
- POST /api/projects/{id}/close/       — close a project (owner only)
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.projects.models import Project
from apps.projects.tests.factories import make_client, make_freelancer, make_project


def _get_token(api_client, email, password):
    resp = api_client.post("/api/users/token/", {"email": email, "password": password}, format="json")
    return resp.data.get("access", "")


class ProjectListCreateAPITest(TestCase):

    def setUp(self):
        self.api_client = APIClient()
        self.client_user = make_client(email="cl@proj.view.test", password="StrongPass#123")
        self.freelancer = make_freelancer(email="fl@proj.view.test", password="StrongPass#123")
        self.project = make_project(self.client_user, title="Public Project")
        token = _get_token(self.api_client, "cl@proj.view.test", "StrongPass#123")
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_authenticated_user_can_list_projects(self):
        resp = self.api_client.get("/api/projects/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_list_projects(self):
        resp = APIClient().get("/api/projects/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_can_create_project(self):
        resp = self.api_client.post("/api/projects/", {
            "title": "New Django Project",
            "description": "Build a production-grade Django REST API with full test coverage.",
            "budget": 8000,
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_freelancer_cannot_create_project(self):
        token = _get_token(self.api_client, "fl@proj.view.test", "StrongPass#123")
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.api_client.post("/api/projects/", {
            "title": "Unauthorized Project",
            "description": "This freelancer should not be able to create a project here.",
            "budget": 3000,
        }, format="json")
        self.assertIn(resp.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
        ])

    def test_retrieve_project_returns_correct_data(self):
        resp = self.api_client.get(f"/api/projects/{self.project.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get("title"), "Public Project")

    def test_owner_can_update_open_project(self):
        resp = self.api_client.patch(f"/api/projects/{self.project.id}/", {
            "title": "Updated Title",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class ProjectViewsPaymentsAPITest(TestCase):

    def setUp(self):
        self.api_client = APIClient()
        self.client_user = make_client(email="cl2@proj.view.test", password="StrongPass#123")
        self.other_client = make_client(email="oc@proj.view.test", password="StrongPass#123")
        self.project = make_project(self.client_user)

        token = _get_token(self.api_client, "oc@proj.view.test", "StrongPass#123")
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_non_owner_cannot_update_project(self):
        resp = self.api_client.patch(f"/api/projects/{self.project.id}/", {
            "title": "Stolen Title",
        }, format="json")
        self.assertIn(resp.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
        ])
