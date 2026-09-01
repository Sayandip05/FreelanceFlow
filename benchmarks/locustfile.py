"""
Master Locust performance test — FreelanceFlow Full Platform.

HOW IT WORKS
------------
1. Run `python manage.py seed_load_test_users` ONCE to create test users.
2. The JSON pool (benchmarks/load_test_credentials.json) is loaded at startup.
3. Each virtual user picks a random credential from the pool and logs in
   at on_start() — no email verification, no throttle issues.

Traffic Mix (weight):
  FreelancerUser  : 4   (40%) — bid, worklog, message, search
  ClientUser      : 2   (20%) — post projects, check payments, review bids
  VisitorUser     : 2   (20%) — search & browse (unauthenticated allowed paths)
  NotifPoller     : 2   (20%) — unread_count polling (most frequent real-world call)

Run (Web UI):
    locust -f benchmarks/locustfile.py --host=http://localhost:8000

Run (Headless smoke test — 60s, 50 users):
    locust -f benchmarks/locustfile.py --host=http://localhost:8000 ^
        --headless --users 50 --spawn-rate 5 --run-time 60s ^
        --html benchmarks/report.html --csv benchmarks/results

Run (Full load test — 5 min, 200 users):
    locust -f benchmarks/locustfile.py --host=http://localhost:8000 ^
        --headless --users 200 --spawn-rate 10 --run-time 300s ^
        --html benchmarks/report.html --csv benchmarks/results
"""
import json
import os
import random
import string

from locust import HttpUser, task, between, events

# ─────────────────────────────────────────────────────────────────────────────
# Load credential pool once at module level
# ─────────────────────────────────────────────────────────────────────────────

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "load_test_credentials.json")
_POOL = {"freelancers": [], "clients": []}

if os.path.exists(CREDENTIALS_FILE):
    with open(CREDENTIALS_FILE) as f:
        _POOL = json.load(f)
    print(
        f"[locustfile] Loaded {len(_POOL['freelancers'])} freelancers "
        f"+ {len(_POOL['clients'])} clients from pool."
    )
else:
    print(
        "[locustfile] WARNING: load_test_credentials.json not found!\n"
        "  Run: python manage.py seed_load_test_users\n"
        "  Then restart locust."
    )


SEARCH_TERMS = [
    "python", "django", "react", "javascript", "machine learning",
    "data science", "nodejs", "flutter", "ui design", "devops", "aws",
]


def random_string(n=6):
    return "".join(random.choices(string.ascii_lowercase, k=n))


def pick_freelancer():
    if _POOL["freelancers"]:
        return random.choice(_POOL["freelancers"])
    return {"email": "freelancer001@loadtest.internal", "password": "LoadTest@123"}


def pick_client():
    if _POOL["clients"]:
        return random.choice(_POOL["clients"])
    return {"email": "client001@loadtest.internal", "password": "LoadTest@123"}


# ─────────────────────────────────────────────────────────────────────────────
# Base mixin with shared login logic
# ─────────────────────────────────────────────────────────────────────────────

class _AuthMixin:
    access_token = None
    refresh_token = None

    def _h(self):
        headers = {"X-Benchmark-Profile": "true"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _login(self, credentials):
        import time
        for attempt in range(3):  # retry up to 3 times on 429
            resp = self.client.post(
                "/api/users/login/",
                json={"email": credentials["email"], "password": credentials["password"]},
                name="/api/users/login/ [setup]",
            )
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("access")
                self.refresh_token = data.get("refresh")
                return
            elif resp.status_code == 429:
                wait = 2 * (attempt + 1)
                print(f"[WARN] 429 throttle for {credentials['email']}, retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"[WARN] Login failed for {credentials['email']}: {resp.status_code} {resp.text[:200]}")
                return

    def _gather_ids(self, url, key):
        """Fetch a list of IDs from a URL. Handles both paginated and flat list responses."""
        r = self.client.get(url, headers=self._h(), name=f"{url} [setup]")
        if r.status_code != 200:
            return []
        try:
            data = r.json()
            # Handle paginated response: {"results": [...], "count": N}
            if isinstance(data, dict):
                items = data.get("results", data.get("data", []))
            # Handle flat list response: [{...}, {...}]
            elif isinstance(data, list):
                items = data
            else:
                return []
            return [item["id"] for item in items[:10] if "id" in item]
        except Exception as e:
            print(f"[WARN] _gather_ids failed for {url}: {e}")
            return []


# ─────────────────────────────────────────────────────────────────────────────
# 1. Visitor — unauthenticated, only hits public endpoints
# ─────────────────────────────────────────────────────────────────────────────

class VisitorUser(HttpUser):
    """
    Unauthenticated visitor browsing public endpoints.
    Only hits endpoints that allow AllowAny permission.
    """
    weight = 2
    wait_time = between(2, 6)

    @task(5)
    def browse_projects_public(self):
        """Project list — test if this is public or needs auth."""
        with self.client.get(
            "/api/projects/",
            name="GET /api/projects/ [anon]",
            catch_response=True,
        ) as r:
            if r.status_code == 401:
                r.success()  # Document that it requires auth — don't count as failure

    @task(5)
    def search_projects_public(self):
        term = random.choice(SEARCH_TERMS)
        with self.client.get(
            f"/api/search/projects/?q={term}",
            name="GET /api/search/projects/ [anon]",
            catch_response=True,
        ) as r:
            if r.status_code == 401:
                r.success()

    @task(4)
    def autocomplete_public(self):
        term = random.choice(SEARCH_TERMS)[:4]
        with self.client.get(
            f"/api/search/autocomplete/?q={term}",
            name="GET /api/search/autocomplete/ [anon]",
            catch_response=True,
        ) as r:
            if r.status_code == 401:
                r.success()

    @task(3)
    def search_freelancers_public(self):
        term = random.choice(SEARCH_TERMS)
        with self.client.get(
            f"/api/search/freelancers/?q={term}",
            name="GET /api/search/freelancers/ [anon]",
            catch_response=True,
        ) as r:
            if r.status_code == 401:
                r.success()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Freelancer — the most common authenticated user
# ─────────────────────────────────────────────────────────────────────────────

class FreelancerUser(_AuthMixin, HttpUser):
    """Active freelancer doing day-to-day platform activity."""

    weight = 4
    wait_time = between(1, 4)

    def on_start(self):
        # Instance-level lists (not class-level) to avoid shared state
        self.bid_ids = []
        self.contract_ids = []
        self.conversation_ids = []
        self.report_ids = []
        self.project_ids = []

        creds = pick_freelancer()
        self._login(creds)
        if not self.access_token:
            return

        self.bid_ids = self._gather_ids("/api/bidding/bids/my_bids/", "bid_ids")
        self.contract_ids = self._gather_ids("/api/bidding/contracts/", "contract_ids")
        self.conversation_ids = self._gather_ids("/api/messaging/conversations/", "conversation_ids")
        self.report_ids = self._gather_ids("/api/worklogs/reports/", "report_ids")
        self.project_ids = self._gather_ids("/api/projects/", "project_ids")

    # ── Auth tasks ────────────────────────────────────────────────────────────

    @task(2)
    def refresh_access_token(self):
        if not self.refresh_token:
            return
        resp = self.client.post(
            "/api/users/token/refresh/",
            json={"refresh": self.refresh_token},
            name="POST /api/users/token/refresh/",
        )
        if resp.status_code == 200:
            self.access_token = resp.json().get("access")

    @task(5)
    def get_my_profile(self):
        self.client.get("/api/users/me/", headers=self._h(), name="GET /api/users/me/")

    # ── Search ────────────────────────────────────────────────────────────────

    @task(3)
    def search_projects(self):
        term = random.choice(SEARCH_TERMS)
        self.client.get(
            f"/api/search/projects/?q={term}",
            headers=self._h(),
            name="GET /api/search/projects/",
        )

    @task(2)
    def autocomplete(self):
        term = random.choice(SEARCH_TERMS)[:4]
        self.client.get(
            f"/api/search/autocomplete/?q={term}",
            headers=self._h(),
            name="GET /api/search/autocomplete/",
        )

    # ── Projects ──────────────────────────────────────────────────────────────

    @task(4)
    def browse_projects(self):
        self.client.get("/api/projects/", headers=self._h(), name="GET /api/projects/")

    @task(2)
    def get_project_detail(self):
        if self.project_ids:
            pk = random.choice(self.project_ids)
            self.client.get(f"/api/projects/{pk}/", headers=self._h(), name="GET /api/projects/<pk>/")

    @task(2)
    def get_my_projects(self):
        self.client.get("/api/projects/my_projects/", headers=self._h(), name="GET /api/projects/my_projects/")

    # ── Bidding ───────────────────────────────────────────────────────────────

    @task(5)
    def list_my_bids(self):
        self.client.get("/api/bidding/bids/my_bids/", headers=self._h(), name="GET /api/bidding/bids/my_bids/")

    @task(3)
    def list_contracts(self):
        self.client.get("/api/bidding/contracts/", headers=self._h(), name="GET /api/bidding/contracts/")

    @task(2)
    def get_contract_detail(self):
        if self.contract_ids:
            pk = random.choice(self.contract_ids)
            self.client.get(f"/api/bidding/contracts/{pk}/", headers=self._h(), name="GET /api/bidding/contracts/<pk>/")

    @task(2)
    def get_pending_approvals(self):
        self.client.get(
            "/api/bidding/worklog-approvals/pending/",
            headers=self._h(),
            name="GET /api/bidding/worklog-approvals/pending/",
        )

    @task(2)
    def get_reviews_received(self):
        self.client.get("/api/bidding/reviews/received/", headers=self._h(), name="GET /api/bidding/reviews/received/")

    @task(1)
    def submit_bid(self):
        if self.project_ids:
            pk = random.choice(self.project_ids)
            self.client.post(
                "/api/bidding/bids/",
                json={
                    "project": pk,
                    "amount": random.randint(100, 3000),
                    "cover_letter": f"Load test proposal {random_string()}. Experienced developer.",
                    "delivery_days": random.randint(7, 30),
                },
                headers=self._h(),
                name="POST /api/bidding/bids/",
            )

    # ── Worklogs ──────────────────────────────────────────────────────────────

    @task(3)
    def list_worklogs(self):
        self.client.get("/api/worklogs/logs/", headers=self._h(), name="GET /api/worklogs/logs/")

    @task(2)
    def list_reports(self):
        self.client.get("/api/worklogs/reports/", headers=self._h(), name="GET /api/worklogs/reports/")

    @task(2)
    def list_deliverables(self):
        self.client.get("/api/worklogs/deliverables/", headers=self._h(), name="GET /api/worklogs/deliverables/")

    # ── Messaging ─────────────────────────────────────────────────────────────

    @task(4)
    def list_conversations(self):
        self.client.get(
            "/api/messaging/conversations/",
            headers=self._h(),
            name="GET /api/messaging/conversations/",
        )

    @task(3)
    def get_conversation_messages(self):
        if self.conversation_ids:
            pk = random.choice(self.conversation_ids)
            self.client.get(
                f"/api/messaging/conversations/{pk}/messages/",
                headers=self._h(),
                name="GET /api/messaging/conversations/<pk>/messages/",
            )

    @task(2)
    def send_message(self):
        if self.conversation_ids:
            pk = random.choice(self.conversation_ids)
            self.client.post(
                f"/api/messaging/conversations/{pk}/send/",
                json={"content": f"Load test msg {random_string()}"},
                headers=self._h(),
                name="POST /api/messaging/conversations/<pk>/send/",
            )

    # ── Notifications ─────────────────────────────────────────────────────────

    @task(6)
    def get_unread_count(self):
        self.client.get(
            "/api/notifications/notifications/unread_count/",
            headers=self._h(),
            name="GET /api/notifications/notifications/unread_count/",
        )

    @task(2)
    def list_notifications(self):
        self.client.get(
            "/api/notifications/notifications/",
            headers=self._h(),
            name="GET /api/notifications/notifications/",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Client — posting projects, reviewing bids, checking payments
# ─────────────────────────────────────────────────────────────────────────────

class ClientUser(_AuthMixin, HttpUser):
    """Authenticated client managing projects and payments."""

    weight = 2
    wait_time = between(2, 5)

    def on_start(self):
        self.project_ids = []
        self.contract_ids = []

        creds = pick_client()
        self._login(creds)
        if not self.access_token:
            return

        self.project_ids = self._gather_ids("/api/projects/my_projects/", "project_ids")
        self.contract_ids = self._gather_ids("/api/bidding/contracts/", "contract_ids")

    @task(5)
    def get_my_profile(self):
        self.client.get("/api/users/me/", headers=self._h(), name="GET /api/users/me/")

    @task(4)
    def list_my_projects(self):
        self.client.get("/api/projects/my_projects/", headers=self._h(), name="GET /api/projects/my_projects/")

    @task(3)
    def search_freelancers(self):
        term = random.choice(SEARCH_TERMS)
        self.client.get(
            f"/api/search/freelancers/?q={term}",
            headers=self._h(),
            name="GET /api/search/freelancers/",
        )

    @task(3)
    def list_contracts(self):
        self.client.get("/api/bidding/contracts/", headers=self._h(), name="GET /api/bidding/contracts/")

    @task(3)
    def get_payment_history(self):
        self.client.get("/api/payments/history/", headers=self._h(), name="GET /api/payments/history/")

    @task(3)
    def get_escrow_status(self):
        if self.contract_ids:
            pk = random.choice(self.contract_ids)
            self.client.post(
                "/api/payments/escrow/",
                json={"contract_id": pk},
                headers=self._h(),
                name="POST /api/payments/escrow/",
            )

    @task(3)
    def get_upcoming_milestones(self):
        self.client.get(
            "/api/payments/milestones/upcoming/",
            headers=self._h(),
            name="GET /api/payments/milestones/upcoming/",
        )

    @task(2)
    def get_milestone_progress(self):
        if self.contract_ids:
            pk = random.choice(self.contract_ids)
            self.client.get(
                f"/api/payments/milestones/{pk}/milestone-progress/",
                headers=self._h(),
                name="GET /api/payments/milestones/<pk>/milestone-progress/",
            )

    @task(6)
    def get_unread_count(self):
        self.client.get(
            "/api/notifications/notifications/unread_count/",
            headers=self._h(),
            name="GET /api/notifications/notifications/unread_count/",
        )

    @task(2)
    def list_bids_for_project(self):
        if self.project_ids:
            pk = random.choice(self.project_ids)
            self.client.get(
                f"/api/projects/{pk}/bids/",
                headers=self._h(),
                name="GET /api/projects/<pk>/bids/",
            )

    @task(1)
    def create_project(self):
        self.client.post(
            "/api/projects/",
            json={
                "title": f"Load Test Project {random_string()}",
                "description": "Performance test project. Looking for an experienced developer.",
                "budget": random.randint(500, 10000),
                "deadline": "2026-12-31",
                "skills": ["Python", "Django", "React"],
            },
            headers=self._h(),
            name="POST /api/projects/",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Notification Poller — simulates the frontend polling unread_count
# ─────────────────────────────────────────────────────────────────────────────

class NotifPollerUser(_AuthMixin, HttpUser):
    """
    Simulates the frontend silently polling for new notifications.
    This is the highest-frequency call in a real-world scenario.
    """

    weight = 2
    wait_time = between(5, 15)  # poll every 5-15 seconds like a real frontend

    def on_start(self):
        self.notification_ids = []

        creds = random.choice([pick_freelancer(), pick_client()])
        self._login(creds)
        if not self.access_token:
            return
        self.notification_ids = self._gather_ids("/api/notifications/notifications/", "notif_ids")

    @task(8)
    def poll_unread_count(self):
        self.client.get(
            "/api/notifications/notifications/unread_count/",
            headers=self._h(),
            name="GET /api/notifications/notifications/unread_count/",
        )

    @task(2)
    def get_unread_list(self):
        self.client.get(
            "/api/notifications/notifications/unread/",
            headers=self._h(),
            name="GET /api/notifications/notifications/unread/",
        )

    @task(1)
    def mark_all_read(self):
        self.client.post(
            "/api/notifications/notifications/mark_all_read/",
            json={},
            headers=self._h(),
            name="POST /api/notifications/notifications/mark_all_read/",
        )
