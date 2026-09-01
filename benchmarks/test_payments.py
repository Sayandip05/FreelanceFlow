"""
Locust performance tests for the Payments app.

Tests:
  - GET  /api/payments/                            (payment list)
  - GET  /api/payments/history/
  - GET  /api/payments/escrow/
  - GET  /api/payments/milestones/<pk>/milestones/
  - GET  /api/payments/milestones/<pk>/milestone-progress/
  - GET  /api/payments/milestones/upcoming/
  - POST /api/payments/milestones/<pk>/fund/       (heavy: calls Razorpay)
  - POST /api/payments/verify/                     (heavy: signature verify)

Run:
    locust -f benchmarks/test_payments.py --host=http://localhost:8000
"""
import random
from locust import HttpUser, task, between


class PaymentsUser(HttpUser):
    """Simulates a client checking payment history and milestone status."""

    wait_time = between(2, 5)

    access_token = None
    contract_ids = []

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

    def on_start(self):
        resp = self.client.post(
            "/api/users/login/",
            json={"email": "client001@loadtest.internal", "password": "LoadTest@123"},
            headers={"X-Benchmark-Profile": "true"},
            name="/api/users/login/ [setup]",
        )
        if resp.status_code == 200:
            self.access_token = resp.json().get("access")

        # Gather contract IDs
        contracts_resp = self.client.get(
            "/api/bidding/contracts/",
            headers=self._auth_headers(),
            name="/api/bidding/contracts/ [setup]",
        )
        if contracts_resp.status_code == 200:
            self.contract_ids = [c["id"] for c in contracts_resp.json().get("results", [])[:10]]

    # ── Tasks ──────────────────────────────────────────────────────────────────

    @task(5)
    def get_payment_history(self):
        self.client.get(
            "/api/payments/history/",
            headers=self._auth_headers(),
            name="GET /api/payments/history/",
        )

    @task(4)
    def get_payment_list(self):
        self.client.get(
            "/api/payments/",
            headers=self._auth_headers(),
            name="GET /api/payments/",
        )

    @task(4)
    def get_escrow_status(self):
        if self.contract_ids:
            pk = random.choice(self.contract_ids)
            self.client.post(
                "/api/payments/escrow/",
                json={"contract_id": pk},
                headers=self._auth_headers(),
                name="POST /api/payments/escrow/",
            )

    @task(3)
    def get_upcoming_milestones(self):
        self.client.get(
            "/api/payments/milestones/upcoming/",
            headers=self._auth_headers(),
            name="GET /api/payments/milestones/upcoming/",
        )

    @task(3)
    def get_milestone_progress(self):
        if self.contract_ids:
            pk = random.choice(self.contract_ids)
            self.client.get(
                f"/api/payments/milestones/{pk}/milestone-progress/",
                headers=self._auth_headers(),
                name="GET /api/payments/milestones/<pk>/milestone-progress/",
            )

    @task(2)
    def get_manage_milestones(self):
        if self.contract_ids:
            pk = random.choice(self.contract_ids)
            self.client.get(
                f"/api/payments/milestones/{pk}/milestones/",
                headers=self._auth_headers(),
                name="GET /api/payments/milestones/<pk>/milestones/",
            )

    @task(1)
    def fund_milestone(self):
        """Heavy task: triggers Razorpay order creation."""
        if self.contract_ids:
            pk = random.choice(self.contract_ids)
            self.client.post(
                f"/api/payments/milestones/{pk}/fund/",
                json={"amount": random.randint(1000, 5000)},
                headers=self._auth_headers(),
                name="POST /api/payments/milestones/<pk>/fund/",
            )
