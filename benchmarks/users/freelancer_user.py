"""
Freelancer User Persona
Simulates realistic marketplace browsing, proposal review, contract management, and worklog flows.
"""
import random
from locust import task, between
from benchmarks.config import TEST_USERS
from benchmarks.users.base_user import AuthenticatedHttpUser


class FreelancerUser(AuthenticatedHttpUser):
    """
    Simulates a Freelancer navigating the platform.
    """
    weight = 5
    wait_time = between(1, 3)
    user_credentials = TEST_USERS["freelancer"]
    discovered_project_ids = []
    discovered_contract_ids = []

    @task(5)
    def browse_projects(self):
        """
        Browse marketplace listings with filtering and pagination.
        """
        res = self.profile_request(
            "GET",
            "/api/projects/?status=OPEN",
            name="[Freelancer] GET /api/projects/?status=OPEN"
        )
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", data if isinstance(data, list) else [])
            if results:
                self.discovered_project_ids = [p["id"] for p in results if "id" in p]

    @task(4)
    def search_projects(self):
        """
        Search projects via full-text / Elasticsearch endpoint.
        """
        query = random.choice(["React", "Python", "Django", "API", "Frontend", "Backend", "AI"])
        self.profile_request(
            "GET",
            f"/api/search/projects/?q={query}",
            name="[Freelancer] GET /api/search/projects/?q={term}"
        )

    @task(3)
    def view_project_detail(self):
        """
        View details of a specific project.
        """
        if not self.discovered_project_ids:
            return
        project_id = random.choice(self.discovered_project_ids)
        self.profile_request(
            "GET",
            f"/api/projects/{project_id}/",
            name="[Freelancer] GET /api/projects/:id/"
        )

    @task(3)
    def view_my_bids(self):
        """
        View list of submitted bids / proposals.
        """
        self.profile_request(
            "GET",
            "/api/bidding/bids/",
            name="[Freelancer] GET /api/bidding/bids/"
        )

    @task(3)
    def view_my_contracts(self):
        """
        View list of active/completed contracts.
        """
        res = self.profile_request(
            "GET",
            "/api/bidding/contracts/",
            name="[Freelancer] GET /api/bidding/contracts/"
        )
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", data if isinstance(data, list) else [])
            if results:
                self.discovered_contract_ids = [c["id"] for c in results if "id" in c]

    @task(2)
    def view_deliverables_and_worklogs(self):
        """
        View submitted deliverables and logged work sessions.
        """
        self.profile_request(
            "GET",
            "/api/worklogs/deliverables/",
            name="[Freelancer] GET /api/worklogs/deliverables/"
        )
        self.profile_request(
            "GET",
            "/api/worklogs/logs/",
            name="[Freelancer] GET /api/worklogs/logs/"
        )

    @task(2)
    def poll_notifications(self):
        """
        Poll unread notifications (triggered periodically by header bell).
        """
        self.profile_request(
            "GET",
            "/api/notifications/unread_count/",
            name="[Common] GET /api/notifications/unread_count/"
        )

    @task(1)
    def view_my_profile(self):
        """
        Retrieve profile details.
        """
        self.profile_request(
            "GET",
            "/api/users/me/",
            name="[Common] GET /api/users/me/"
        )
