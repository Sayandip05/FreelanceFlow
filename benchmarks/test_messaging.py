"""
Locust performance tests for the Messaging app.

Tests:
  - GET  /api/messaging/conversations/
  - GET  /api/messaging/conversations/<pk>/messages/
  - POST /api/messaging/conversations/<pk>/send/
  - POST /api/messaging/conversations/<pk>/mark_read/
  - GET  /api/messaging/messages/

Run:
    locust -f benchmarks/test_messaging.py --host=http://localhost:8000
"""
import random
import string
from locust import HttpUser, task, between


def random_string(n=8):
    return "".join(random.choices(string.ascii_lowercase, k=n))


class MessagingUser(HttpUser):
    """Simulates a user browsing and sending chat messages."""

    wait_time = between(1, 3)

    access_token = None
    conversation_ids = []

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

        # Gather conversation IDs
        conv_resp = self.client.get(
            "/api/messaging/conversations/",
            headers=self._auth_headers(),
            name="/api/messaging/conversations/ [setup]",
        )
        if conv_resp.status_code == 200:
            self.conversation_ids = [c["id"] for c in conv_resp.json().get("results", [])[:10]]

    # ── Tasks ──────────────────────────────────────────────────────────────────

    @task(6)
    def list_conversations(self):
        self.client.get(
            "/api/messaging/conversations/",
            headers=self._auth_headers(),
            name="GET /api/messaging/conversations/",
        )

    @task(5)
    def get_conversation_messages(self):
        """Fetching message history — can be expensive for long conversations."""
        if self.conversation_ids:
            pk = random.choice(self.conversation_ids)
            self.client.get(
                f"/api/messaging/conversations/{pk}/messages/",
                headers=self._auth_headers(),
                name="GET /api/messaging/conversations/<pk>/messages/",
            )

    @task(4)
    def send_message(self):
        """Sending a message — must feel instant to the user."""
        if self.conversation_ids:
            pk = random.choice(self.conversation_ids)
            self.client.post(
                f"/api/messaging/conversations/{pk}/send/",
                json={"content": f"Load test message {random_string(6)}"},
                headers=self._auth_headers(),
                name="POST /api/messaging/conversations/<pk>/send/",
            )

    @task(2)
    def mark_conversation_read(self):
        if self.conversation_ids:
            pk = random.choice(self.conversation_ids)
            self.client.post(
                f"/api/messaging/conversations/{pk}/mark_read/",
                json={},
                headers=self._auth_headers(),
                name="POST /api/messaging/conversations/<pk>/mark_read/",
            )

    @task(1)
    def list_messages(self):
        self.client.get(
            "/api/messaging/messages/",
            headers=self._auth_headers(),
            name="GET /api/messaging/messages/",
        )
