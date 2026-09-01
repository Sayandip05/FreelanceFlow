"""
Locust performance tests for the Users app.

Tests:
  - POST /api/users/register/
  - POST /api/users/login/
  - GET  /api/users/me/
  - POST /api/users/token/refresh/
  - PUT  /api/users/me/      (profile update)
  - GET  /api/users/<pk>/
  - PATCH /api/users/availability/
  - GET  /api/users/activity/
  - GET  /api/users/status/online/
  - GET  /api/users/status/count/

Run:
    locust -f benchmarks/test_users.py --host=http://localhost:8000
"""
import random
import string
from locust import HttpUser, task, between


def random_string(n=8):
    return "".join(random.choices(string.ascii_lowercase, k=n))


class UsersUser(HttpUser):
    """Simulates a user going through auth and profile flows."""

    wait_time = between(1, 3)

    # Credentials injected after login
    access_token = None
    refresh_token = None
    user_id = None

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _auth_headers(self):
        headers = {"X-Benchmark-Profile": "true"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_start(self):
        """Register a fresh user then log in to get tokens."""
        username = f"load_{random_string()}"
        email = f"{username}@loadtest.com"
        password = "LoadTest@123"

        # Register
        self.client.post(
            "/api/users/register/",
            json={
                "username": username,
                "email": email,
                "password": password,
                "password2": password,
                "role": "freelancer",
                "first_name": "Load",
                "last_name": "Tester",
            },
            headers={"X-Benchmark-Profile": "true"},
            name="/api/users/register/ [setup]",
        )

        # Login
        resp = self.client.post(
            "/api/users/login/",
            json={"email": email, "password": password},
            headers={"X-Benchmark-Profile": "true"},
            name="/api/users/login/ [setup]",
        )
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data.get("access")
            self.refresh_token = data.get("refresh")
            self.user_id = data.get("user", {}).get("id")

    # ── Tasks ─────────────────────────────────────────────────────────────────

    @task(5)
    def get_my_profile(self):
        self.client.get("/api/users/me/", headers=self._auth_headers(), name="GET /api/users/me/")

    @task(3)
    def refresh_token(self):
        if self.refresh_token:
            resp = self.client.post(
                "/api/users/token/refresh/",
                json={"refresh": self.refresh_token},
                name="POST /api/users/token/refresh/",
            )
            if resp.status_code == 200:
                self.access_token = resp.json().get("access")

    @task(2)
    def update_profile(self):
        self.client.patch(
            "/api/users/me/",
            json={"bio": f"Updated bio {random_string(6)}"},
            headers=self._auth_headers(),
            name="PATCH /api/users/me/",
        )

    @task(2)
    def get_activity_log(self):
        self.client.get(
            "/api/users/activity/",
            headers=self._auth_headers(),
            name="GET /api/users/activity/",
        )

    @task(2)
    def get_online_users(self):
        self.client.get(
            "/api/users/status/online/",
            headers=self._auth_headers(),
            name="GET /api/users/status/online/",
        )

    @task(1)
    def get_online_count(self):
        self.client.get(
            "/api/users/status/count/",
            headers=self._auth_headers(),
            name="GET /api/users/status/count/",
        )

    @task(1)
    def toggle_availability(self):
        self.client.patch(
            "/api/users/availability/",
            json={},
            headers=self._auth_headers(),
            name="PATCH /api/users/availability/",
        )

    @task(1)
    def get_user_detail(self):
        if self.user_id:
            self.client.get(
                f"/api/users/{self.user_id}/",
                headers=self._auth_headers(),
                name="GET /api/users/<pk>/",
            )
