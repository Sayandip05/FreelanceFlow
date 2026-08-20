"""
Locust performance tests for the Projects app.

Tests:
  - GET  /api/projects/          (project listing — marketplace)
  - POST /api/projects/          (create a project)
  - GET  /api/projects/<pk>/     (project detail)
  - GET  /api/projects/<pk>/bids/
  - GET  /api/projects/my_projects/
  - POST /api/projects/bookmarks/<pk>/bookmark/
  - GET  /api/projects/bookmarks/my-bookmarks/

Run:
    locust -f benchmarks/test_projects.py --host=http://localhost:8000
"""
import random
import string
from locust import HttpUser, task, between


def random_string(n=8):
    return "".join(random.choices(string.ascii_lowercase, k=n))


class ProjectsUser(HttpUser):
    """Simulates a client browsing and posting projects."""

    wait_time = between(1, 4)

    access_token = None
    project_ids = []

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

    def on_start(self):
        """Log in as a pre-seeded client user."""
        resp = self.client.post(
            "/api/users/login/",
            json={"email": "client@loadtest.com", "password": "LoadTest@123"},
            name="/api/users/login/ [setup]",
        )
        if resp.status_code == 200:
            self.access_token = resp.json().get("access")

        # Seed project IDs for detail/bid reads
        list_resp = self.client.get(
            "/api/projects/",
            headers=self._auth_headers(),
            name="/api/projects/ [setup]",
        )
        if list_resp.status_code == 200:
            results = list_resp.json().get("results", [])
            self.project_ids = [p["id"] for p in results[:20]]

    # ── Tasks ──────────────────────────────────────────────────────────────────

    @task(6)
    def list_projects(self):
        self.client.get(
            "/api/projects/",
            headers=self._auth_headers(),
            name="GET /api/projects/",
        )

    @task(4)
    def get_project_detail(self):
        if self.project_ids:
            pk = random.choice(self.project_ids)
            self.client.get(
                f"/api/projects/{pk}/",
                headers=self._auth_headers(),
                name="GET /api/projects/<pk>/",
            )

    @task(3)
    def get_project_bids(self):
        if self.project_ids:
            pk = random.choice(self.project_ids)
            self.client.get(
                f"/api/projects/{pk}/bids/",
                headers=self._auth_headers(),
                name="GET /api/projects/<pk>/bids/",
            )

    @task(2)
    def get_my_projects(self):
        self.client.get(
            "/api/projects/my_projects/",
            headers=self._auth_headers(),
            name="GET /api/projects/my_projects/",
        )

    @task(2)
    def get_my_bookmarks(self):
        self.client.get(
            "/api/projects/bookmarks/my-bookmarks/",
            headers=self._auth_headers(),
            name="GET /api/projects/bookmarks/my-bookmarks/",
        )

    @task(1)
    def create_project(self):
        self.client.post(
            "/api/projects/",
            json={
                "title": f"Load Test Project {random_string(5)}",
                "description": "Performance test project description with enough detail.",
                "budget": random.randint(500, 5000),
                "deadline": "2026-12-31",
                "skills": ["Python", "Django"],
            },
            headers=self._auth_headers(),
            name="POST /api/projects/",
        )

    @task(1)
    def bookmark_project(self):
        if self.project_ids:
            pk = random.choice(self.project_ids)
            self.client.post(
                f"/api/projects/bookmarks/{pk}/bookmark/",
                json={},
                headers=self._auth_headers(),
                name="POST /api/projects/bookmarks/<pk>/bookmark/",
            )
