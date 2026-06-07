"""
Tests for apps.projects.services.

Coverage:
- create_project: happy path with/without skills, client-only, missing title/desc, zero budget
- update_project: owner can update, non-owner denied, non-OPEN project denied, budget validation
- close_project: owner can close, non-owner denied, completed project denied
- mark_project_in_progress: only OPEN project transitions
- mark_project_completed: only IN_PROGRESS project transitions
"""
from django.test import TestCase

from apps.projects.models import Project, ProjectSkill
from apps.projects.services import (
    create_project,
    update_project,
    close_project,
    mark_project_in_progress,
    mark_project_completed,
)
from apps.projects.tests.factories import make_client, make_freelancer, make_project
from core.exceptions import ValidationError, PermissionDeniedError


class CreateProjectServiceTest(TestCase):

    def setUp(self):
        self.client_user = make_client()
        self.freelancer = make_freelancer()

    def test_create_project_succeeds(self):
        project = create_project(
            client=self.client_user,
            title="Web App",
            description="Build a Django REST API backend for our platform.",
            budget=5000,
        )
        self.assertIsNotNone(project.pk)
        self.assertEqual(project.status, Project.Status.OPEN)

    def test_create_project_with_skills_creates_skills(self):
        project = create_project(
            client=self.client_user,
            title="Web App",
            description="Build a Django REST API backend for our platform.",
            budget=5000,
            skills=["Python", "Django", "PostgreSQL"],
        )
        skill_names = list(project.skills.values_list("skill_name", flat=True))
        self.assertIn("Python", skill_names)
        self.assertIn("Django", skill_names)
        self.assertIn("PostgreSQL", skill_names)

    def test_create_project_strips_empty_skills(self):
        project = create_project(
            client=self.client_user,
            title="Web App",
            description="Build a Django REST API backend for our platform.",
            budget=5000,
            skills=["Python", " ", ""],
        )
        self.assertEqual(project.skills.count(), 1)

    def test_freelancer_cannot_create_project(self):
        with self.assertRaises(PermissionDeniedError):
            create_project(
                client=self.freelancer,
                title="Web App",
                description="Some description text here.",
                budget=5000,
            )

    def test_raises_on_empty_title(self):
        with self.assertRaises(ValidationError) as ctx:
            create_project(self.client_user, title="", description="Desc.", budget=5000)
        self.assertEqual(ctx.exception.field, "title")

    def test_raises_on_empty_description(self):
        with self.assertRaises(ValidationError) as ctx:
            create_project(self.client_user, title="Title", description="", budget=5000)
        self.assertEqual(ctx.exception.field, "description")

    def test_raises_on_zero_budget(self):
        with self.assertRaises(ValidationError) as ctx:
            create_project(self.client_user, title="T", description="Desc", budget=0)
        self.assertEqual(ctx.exception.field, "budget")

    def test_raises_on_negative_budget(self):
        with self.assertRaises(ValidationError) as ctx:
            create_project(self.client_user, title="T", description="Desc", budget=-100)
        self.assertEqual(ctx.exception.field, "budget")


class UpdateProjectServiceTest(TestCase):

    def setUp(self):
        self.client_user = make_client()
        self.other_client = make_client(email="other@test.com")
        self.project = make_project(self.client_user, title="Original Title", budget=3000)

    def test_owner_can_update_title(self):
        updated = update_project(self.project, self.client_user, title="New Title")
        self.assertEqual(updated.title, "New Title")

    def test_owner_can_update_budget(self):
        updated = update_project(self.project, self.client_user, budget=9000)
        self.assertEqual(float(updated.budget), 9000)

    def test_owner_can_replace_skills(self):
        update_project(self.project, self.client_user, skills=["Rust", "WASM"])
        skills = list(self.project.skills.values_list("skill_name", flat=True))
        self.assertIn("Rust", skills)
        self.assertNotIn("Python", skills)

    def test_non_owner_cannot_update(self):
        with self.assertRaises(PermissionDeniedError):
            update_project(self.project, self.other_client, title="Stolen")

    def test_non_open_project_cannot_be_updated(self):
        self.project.status = Project.Status.IN_PROGRESS
        self.project.save()
        with self.assertRaises(ValidationError) as ctx:
            update_project(self.project, self.client_user, title="New")
        self.assertEqual(ctx.exception.field, "status")

    def test_update_budget_to_zero_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            update_project(self.project, self.client_user, budget=0)
        self.assertEqual(ctx.exception.field, "budget")


class CloseProjectServiceTest(TestCase):

    def setUp(self):
        self.client_user = make_client()
        self.other_client = make_client(email="other@test.com")
        self.project = make_project(self.client_user)

    def test_owner_can_close_open_project(self):
        closed = close_project(self.project, self.client_user)
        self.assertEqual(closed.status, Project.Status.CANCELLED)

    def test_non_owner_cannot_close(self):
        with self.assertRaises(PermissionDeniedError):
            close_project(self.project, self.other_client)

    def test_completed_project_cannot_be_closed(self):
        self.project.status = Project.Status.COMPLETED
        self.project.save()
        with self.assertRaises(ValidationError):
            close_project(self.project, self.client_user)


class ProjectStatusTransitionTest(TestCase):

    def setUp(self):
        self.client_user = make_client()
        self.project = make_project(self.client_user)

    def test_mark_in_progress_from_open(self):
        updated = mark_project_in_progress(self.project)
        self.assertEqual(updated.status, Project.Status.IN_PROGRESS)

    def test_mark_in_progress_from_non_open_raises(self):
        self.project.status = Project.Status.IN_PROGRESS
        self.project.save()
        with self.assertRaises(ValidationError):
            mark_project_in_progress(self.project)

    def test_mark_completed_from_in_progress(self):
        self.project.status = Project.Status.IN_PROGRESS
        self.project.save()
        updated = mark_project_completed(self.project)
        self.assertEqual(updated.status, Project.Status.COMPLETED)

    def test_mark_completed_from_open_raises(self):
        with self.assertRaises(ValidationError):
            mark_project_completed(self.project)
