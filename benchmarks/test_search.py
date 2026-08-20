"""
Locust performance tests for the Search app.

Tests:
  - GET /api/search/                 (combined search)
  - GET /api/search/projects/        (project full-text search)
  - GET /api/search/freelancers/     (freelancer full-text search)
  - GET /api/search/autocomplete/    (autocomplete suggestions)

Run:
    locust -f benchmarks/test_search.py --host=http://localhost:8000
"""
import random
from locust import HttpUser, task, between

SEARCH_TERMS = [
    "python", "django", "react", "javascript", "machine learning",
    "data science", "nodejs", "flutter", "android", "ui design",
    "devops", "aws", "docker", "api", "backend"
]


class SearchUser(HttpUser):
    """Simulates a user performing search operations."""

    wait_time = between(1, 3)

    access_token = None

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

    def on_start(self):
        resp = self.client.post(
            "/api/users/login/",
            json={"email": "freelancer@loadtest.com", "password": "LoadTest@123"},
            name="/api/users/login/ [setup]",
        )
        if resp.status_code == 200:
            self.access_token = resp.json().get("access")

    # ── Tasks ──────────────────────────────────────────────────────────────────

    @task(5)
    def search_projects(self):
        """Full Elasticsearch query on the projects index."""
        term = random.choice(SEARCH_TERMS)
        self.client.get(
            f"/api/search/projects/?q={term}",
            headers=self._auth_headers(),
            name="GET /api/search/projects/",
        )

    @task(4)
    def search_freelancers(self):
        """Full Elasticsearch query on the freelancers index."""
        term = random.choice(SEARCH_TERMS)
        self.client.get(
            f"/api/search/freelancers/?q={term}",
            headers=self._auth_headers(),
            name="GET /api/search/freelancers/",
        )

    @task(3)
    def general_search(self):
        """Combined search across both indexes."""
        term = random.choice(SEARCH_TERMS)
        self.client.get(
            f"/api/search/?q={term}",
            headers=self._auth_headers(),
            name="GET /api/search/",
        )

    @task(4)
    def autocomplete(self):
        """Autocomplete — called on every keystroke, must be very fast."""
        term = random.choice(SEARCH_TERMS)[:4]  # simulate partial typing
        self.client.get(
            f"/api/search/autocomplete/?q={term}",
            headers=self._auth_headers(),
            name="GET /api/search/autocomplete/",
        )
