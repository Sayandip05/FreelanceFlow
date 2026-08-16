"""
Client User Persona
Simulates realistic Client flows: viewing proposals, contract oversight, reviewing deliverables, and escrow payments.
"""
import random
from locust import task, between
from benchmarks.config import TEST_USERS
from benchmarks.users.base_user import AuthenticatedHttpUser


class ClientUser(AuthenticatedHttpUser):
    """
    Simulates a Client managing projects and reviewing milestones.
    """
    weight = 4
    wait_time = between(1, 3)
    user_credentials = TEST_USERS["client"]
    my_project_ids = []
    active_contract_ids = []

    def on_start(self):
        super().on_start()
        # Seed user projects and contracts
        res = self.client.get("/api/projects/")
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", data if isinstance(data, list) else [])
            self.my_project_ids = [p["id"] for p in results if "id" in p]

    @task(4)
    def view_contracts(self):
        """
        View client contracts list.
        """
        res = self.profile_request(
            "GET",
            "/api/bidding/contracts/",
            name="[Client] GET /api/bidding/contracts/"
        )
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", data if isinstance(data, list) else [])
            if results:
                self.active_contract_ids = [c["id"] for c in results if "id" in c]

    @task(3)
    def view_project_proposals(self):
        """
        View proposals submitted for a specific client project.
        """
        if not self.my_project_ids:
            return
        project_id = random.choice(self.my_project_ids)
        self.profile_request(
            "GET",
            f"/api/bidding/bids/?project={project_id}",
            name="[Client] GET /api/bidding/bids/?project=:id"
        )


    @task(3)
    def inspect_deliverables(self):
        """
        Inspect deliverables submitted by freelancers for milestone review.
        """
        self.profile_request(
            "GET",
            "/api/worklogs/deliverables/",
            name="[Client] GET /api/worklogs/deliverables/"
        )

    @task(3)
    def view_financial_summary(self):
        """
        View payments and milestones.
        """
        self.profile_request(
            "GET",
            "/api/payments/",
            name="[Client] GET /api/payments/"
        )
        self.profile_request(
            "GET",
            "/api/payments/milestones/",
            name="[Client] GET /api/payments/milestones/"
        )

    @task(2)
    def search_freelancers(self):
        """
        Search freelancer directory via Elasticsearch.
        """
        query = random.choice(["Django", "React", "Fullstack", "API", "Frontend"])
        self.profile_request(
            "GET",
            f"/api/search/freelancers/?q={query}",
            name="[Client] GET /api/search/freelancers/?q={term}"
        )

    @task(2)
    def poll_notifications(self):
        """
        Poll notifications badge.
        """
        self.profile_request(
            "GET",
            "/api/notifications/unread_count/",
            name="[Common] GET /api/notifications/unread_count/"
        )

    @task(1)
    def view_notifications_list(self):
        """
        Fetch full notification list for header popover.
        """
        self.profile_request(
            "GET",
            "/api/notifications/",
            name="[Common] GET /api/notifications/"
        )
