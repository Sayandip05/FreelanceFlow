"""
Locust performance tests for the Worklogs app.

Tests:
  - GET  /api/worklogs/logs/
  - POST /api/worklogs/logs/                            (log hours)
  - GET  /api/worklogs/reports/
  - GET  /api/worklogs/reports/<pk>/
  - GET  /api/worklogs/deliverables/
  - GET  /api/worklogs/deliverables/<pk>/
  - GET  /api/worklogs/report-schedule/
  - GET  /api/worklogs/ai/history/
  - POST /api/worklogs/ai/chat/                         (AI call — heavy)
  - GET  /api/worklogs/ai/context/

Run:
    locust -f benchmarks/test_worklogs.py --host=http://localhost:8000
"""
import random
import string
from datetime import date
from locust import HttpUser, task, between


def random_string(n=8):
    return "".join(random.choices(string.ascii_lowercase, k=n))


class WorklogsUser(HttpUser):
    """Simulates a freelancer interacting with work logs, AI chat, and reports."""

    wait_time = between(2, 5)

    access_token = None
    report_ids = []
    deliverable_ids = []
    contract_ids = []

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

        reports_resp = self.client.get(
            "/api/worklogs/reports/",
            headers=self._auth_headers(),
            name="/api/worklogs/reports/ [setup]",
        )
        if reports_resp.status_code == 200:
            self.report_ids = [r["id"] for r in reports_resp.json().get("results", [])[:10]]

        deliv_resp = self.client.get(
            "/api/worklogs/deliverables/",
            headers=self._auth_headers(),
            name="/api/worklogs/deliverables/ [setup]",
        )
        if deliv_resp.status_code == 200:
            self.deliverable_ids = [d["id"] for d in deliv_resp.json().get("results", [])[:10]]

        contracts_resp = self.client.get(
            "/api/bidding/contracts/",
            headers=self._auth_headers(),
            name="/api/bidding/contracts/ [setup]",
        )
        if contracts_resp.status_code == 200:
            self.contract_ids = [c["id"] for c in contracts_resp.json().get("results", [])[:5]]

    # ── Tasks ──────────────────────────────────────────────────────────────────

    @task(5)
    def list_worklogs(self):
        self.client.get(
            "/api/worklogs/logs/",
            headers=self._auth_headers(),
            name="GET /api/worklogs/logs/",
        )

    @task(4)
    def list_reports(self):
        self.client.get(
            "/api/worklogs/reports/",
            headers=self._auth_headers(),
            name="GET /api/worklogs/reports/",
        )

    @task(3)
    def get_report_detail(self):
        if self.report_ids:
            pk = random.choice(self.report_ids)
            self.client.get(
                f"/api/worklogs/reports/{pk}/",
                headers=self._auth_headers(),
                name="GET /api/worklogs/reports/<pk>/",
            )

    @task(3)
    def list_deliverables(self):
        self.client.get(
            "/api/worklogs/deliverables/",
            headers=self._auth_headers(),
            name="GET /api/worklogs/deliverables/",
        )

    @task(2)
    def get_deliverable_detail(self):
        if self.deliverable_ids:
            pk = random.choice(self.deliverable_ids)
            self.client.get(
                f"/api/worklogs/deliverables/{pk}/",
                headers=self._auth_headers(),
                name="GET /api/worklogs/deliverables/<pk>/",
            )

    @task(2)
    def list_report_schedules(self):
        self.client.get(
            "/api/worklogs/report-schedule/",
            headers=self._auth_headers(),
            name="GET /api/worklogs/report-schedule/",
        )

    @task(2)
    def get_ai_history(self):
        self.client.get(
            "/api/worklogs/ai/history/",
            headers=self._auth_headers(),
            name="GET /api/worklogs/ai/history/",
        )

    @task(2)
    def get_ai_context(self):
        self.client.get(
            "/api/worklogs/ai/context/",
            headers=self._auth_headers(),
            name="GET /api/worklogs/ai/context/",
        )

    @task(2)
    def log_hours(self):
        """Create a work log entry."""
        if self.contract_ids:
            pk = random.choice(self.contract_ids)
            self.client.post(
                "/api/worklogs/logs/",
                json={
                    "contract": pk,
                    "date": date.today().isoformat(),
                    "hours_worked": round(random.uniform(1.0, 8.0), 1),
                    "description": f"Load test work log {random_string(6)}",
                },
                headers=self._auth_headers(),
                name="POST /api/worklogs/logs/",
            )

    @task(1)
    def ai_chat(self):
        """AI chat message — hits Gemini/Groq, will be naturally slow."""
        self.client.post(
            "/api/worklogs/ai/chat/",
            json={"message": "Summarize my recent work progress"},
            headers=self._auth_headers(),
            name="POST /api/worklogs/ai/chat/",
        )
