"""
Locust performance tests for the Bidding app.

Tests:
  - GET  /api/bidding/bids/              (list bids)
  - POST /api/bidding/bids/              (submit a bid)
  - GET  /api/bidding/bids/<pk>/
  - GET  /api/bidding/bids/my_bids/
  - GET  /api/bidding/contracts/         (list contracts)
  - GET  /api/bidding/contracts/<pk>/
  - GET  /api/bidding/reviews/
  - GET  /api/bidding/reviews/received/
  - GET  /api/bidding/reviews/given/
  - GET  /api/bidding/counter-offers/pending/
  - GET  /api/bidding/counter-offers/stats/
  - GET  /api/bidding/worklog-approvals/pending/

Run:
    locust -f benchmarks/test_bidding.py --host=http://localhost:8000
"""
import random
import string
from locust import HttpUser, task, between


def random_string(n=8):
    return "".join(random.choices(string.ascii_lowercase, k=n))


class BiddingUser(HttpUser):
    """Simulates a freelancer browsing, bidding, and checking contracts."""

    wait_time = between(1, 3)

    access_token = None
    bid_ids = []
    contract_ids = []
    project_ids = []

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

    def on_start(self):
        resp = self.client.post(
            "/api/users/login/",
            json={"email": "freelancer001@loadtest.internal", "password": "LoadTest@123"},
            headers={"X-Benchmark-Profile": "true"},
            name="/api/users/login/ [setup]",
        )
        if resp.status_code == 200:
            self.access_token = resp.json().get("access")

        # Gather IDs for read tasks
        bids_resp = self.client.get("/api/bidding/bids/", headers=self._auth_headers(), name="/api/bidding/bids/ [setup]")
        if bids_resp.status_code == 200:
            self.bid_ids = [b["id"] for b in bids_resp.json().get("results", [])[:10]]

        contracts_resp = self.client.get("/api/bidding/contracts/", headers=self._auth_headers(), name="/api/bidding/contracts/ [setup]")
        if contracts_resp.status_code == 200:
            self.contract_ids = [c["id"] for c in contracts_resp.json().get("results", [])[:10]]

        projects_resp = self.client.get("/api/projects/", headers=self._auth_headers(), name="/api/projects/ [setup]")
        if projects_resp.status_code == 200:
            self.project_ids = [p["id"] for p in projects_resp.json().get("results", [])[:10]]

    # ── Tasks ──────────────────────────────────────────────────────────────────

    @task(5)
    def list_my_bids(self):
        self.client.get(
            "/api/bidding/bids/my_bids/",
            headers=self._auth_headers(),
            name="GET /api/bidding/bids/my_bids/",
        )

    @task(4)
    def list_bids(self):
        self.client.get(
            "/api/bidding/bids/",
            headers=self._auth_headers(),
            name="GET /api/bidding/bids/",
        )

    @task(3)
    def list_contracts(self):
        self.client.get(
            "/api/bidding/contracts/",
            headers=self._auth_headers(),
            name="GET /api/bidding/contracts/",
        )

    @task(3)
    def get_contract_detail(self):
        if self.contract_ids:
            pk = random.choice(self.contract_ids)
            self.client.get(
                f"/api/bidding/contracts/{pk}/",
                headers=self._auth_headers(),
                name="GET /api/bidding/contracts/<pk>/",
            )

    @task(2)
    def get_bid_detail(self):
        if self.bid_ids:
            pk = random.choice(self.bid_ids)
            self.client.get(
                f"/api/bidding/bids/{pk}/",
                headers=self._auth_headers(),
                name="GET /api/bidding/bids/<pk>/",
            )

    @task(2)
    def get_reviews_received(self):
        self.client.get(
            "/api/bidding/reviews/received/",
            headers=self._auth_headers(),
            name="GET /api/bidding/reviews/received/",
        )

    @task(2)
    def get_reviews_given(self):
        self.client.get(
            "/api/bidding/reviews/given/",
            headers=self._auth_headers(),
            name="GET /api/bidding/reviews/given/",
        )

    @task(2)
    def get_pending_approvals(self):
        self.client.get(
            "/api/bidding/worklog-approvals/pending/",
            headers=self._auth_headers(),
            name="GET /api/bidding/worklog-approvals/pending/",
        )

    @task(1)
    def get_counter_offer_stats(self):
        self.client.get(
            "/api/bidding/counter-offers/stats/",
            headers=self._auth_headers(),
            name="GET /api/bidding/counter-offers/stats/",
        )

    @task(1)
    def get_pending_counter_offers(self):
        self.client.get(
            "/api/bidding/counter-offers/pending/",
            headers=self._auth_headers(),
            name="GET /api/bidding/counter-offers/pending/",
        )

    @task(1)
    def submit_bid(self):
        if self.project_ids:
            pk = random.choice(self.project_ids)
            self.client.post(
                "/api/bidding/bids/",
                json={
                    "project": pk,
                    "amount": random.randint(100, 3000),
                    "cover_letter": f"Load test proposal {random_string(6)}. I have experience with this.",
                    "delivery_days": random.randint(7, 30),
                },
                headers=self._auth_headers(),
                name="POST /api/bidding/bids/",
            )
