"""
Tests for apps.projects models.

Coverage:
- Project: creation, __str__, Status choices, ordering
- ProjectSkill: creation, __str__, unique_together constraint
"""
from django.test import TestCase
from django.db import IntegrityError

from apps.projects.models import Project, ProjectSkill
from apps.projects.tests.factories import make_client, make_project


class ProjectModelTest(TestCase):

    def setUp(self):
        self.client_user = make_client()
        self.project = make_project(self.client_user, title="My Test Project")

    def test_project_str(self):
        self.assertEqual(str(self.project), "My Test Project (OPEN)")

    def test_default_status_is_open(self):
        self.assertEqual(self.project.status, Project.Status.OPEN)

    def test_project_client_fk(self):
        self.assertEqual(self.project.client, self.client_user)

    def test_project_ordering_latest_first(self):
        p2 = make_project(self.client_user, title="Second Project")
        projects = list(Project.objects.all())
        # p2 is created later so should be first in -created_at ordering
        self.assertEqual(projects[0], p2)


class ProjectSkillModelTest(TestCase):

    def setUp(self):
        self.client_user = make_client()
        self.project = make_project(self.client_user, skills=["Python"])

    def test_skill_str(self):
        skill = self.project.skills.first()
        self.assertEqual(str(skill), "My Test Project - Python")

    def test_skill_name_stored_correctly(self):
        skill = self.project.skills.get(skill_name="Python")
        self.assertIsNotNone(skill)

    def test_unique_together_prevents_duplicate_skill(self):
        with self.assertRaises(Exception):
            ProjectSkill.objects.create(project=self.project, skill_name="Python")
