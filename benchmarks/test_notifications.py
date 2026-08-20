"""
Locust performance tests for the Notifications app.

Tests:
  - GET  /api/notifications/notifications/             (list)
  - GET  /api/notifications/notifications/unread/
  - GET  /api/notifications/notifications/unread_count/ (polled very frequently)
  - POST /api/notifications/notifications/<pk>/mark_read/
  - POST /api/notifications/notifications/mark_all_read/
  - DELETE /api/notifications/notifications/<pk>/delete/

Run:
    locust -f benchmarks/test_notifications.py --host=http://localhost:8000
"""
import random
from locust import HttpUser, task, between


class NotificationsUser(HttpUser):
    """Simulates a user polling and interacting with their notifications."""

    wait_time = between(1, 2)

    access_token = None
    notification_ids = []

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

        notif_resp = self.client.get(
            "/api/notifications/notifications/",
            headers=self._auth_headers(),
            name="/api/notifications/notifications/ [setup]",
        )
        if notif_resp.status_code == 200:
            self.notification_ids = [n["id"] for n in notif_resp.json().get("results", [])[:20]]

    # ── Tasks ──────────────────────────────────────────────────────────────────

    @task(8)
    def get_unread_count(self):
        """Most frequently polled endpoint — called on every dashboard render."""
        self.client.get(
            "/api/notifications/notifications/unread_count/",
            headers=self._auth_headers(),
            name="GET /api/notifications/notifications/unread_count/",
        )

    @task(4)
    def list_notifications(self):
        self.client.get(
            "/api/notifications/notifications/",
            headers=self._auth_headers(),
            name="GET /api/notifications/notifications/",
        )

    @task(3)
    def get_unread_notifications(self):
        self.client.get(
            "/api/notifications/notifications/unread/",
            headers=self._auth_headers(),
            name="GET /api/notifications/notifications/unread/",
        )

    @task(2)
    def mark_one_read(self):
        if self.notification_ids:
            pk = random.choice(self.notification_ids)
            self.client.post(
                f"/api/notifications/notifications/{pk}/mark_read/",
                json={},
                headers=self._auth_headers(),
                name="POST /api/notifications/notifications/<pk>/mark_read/",
            )

    @task(1)
    def mark_all_read(self):
        self.client.post(
            "/api/notifications/notifications/mark_all_read/",
            json={},
            headers=self._auth_headers(),
            name="POST /api/notifications/notifications/mark_all_read/",
        )

    @task(1)
    def delete_notification(self):
        if self.notification_ids:
            pk = random.choice(self.notification_ids)
            self.client.post(
                f"/api/notifications/notifications/{pk}/delete/",
                json={},
                headers=self._auth_headers(),
                name="POST /api/notifications/notifications/<pk>/delete/",
            )
