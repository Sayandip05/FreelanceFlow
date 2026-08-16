"""
Public Unauthenticated User Persona
Simulates unauthenticated visitors browsing open projects catalog, autocomplete search, keyword search, and OAuth init.
"""
import random
from locust import HttpUser, task, between


class PublicUser(HttpUser):
    """
    Simulates anonymous traffic browsing public search and auth initiation endpoints.
    """
    weight = 2
    wait_time = between(1, 3)

    @task(4)
    def browse_public_catalog(self):
        """
        Browse public projects catalog.
        """
        self.client.get(
            "/api/projects/",
            name="[Public] GET /api/projects/"
        )

    @task(3)
    def autocomplete_search(self):
        """
        Type-ahead autocomplete queries.
        """
        prefix = random.choice(["re", "py", "dj", "we", "fr", "ap", "ai", "fu"])
        self.client.get(
            f"/api/search/autocomplete/?q={prefix}",
            name="[Public] GET /api/search/autocomplete/?q={prefix}"
        )

    @task(3)
    def public_project_search(self):
        """
        Public keyword search on open projects catalog.
        """
        query = random.choice(["React", "Python", "API", "Frontend", "Backend", "AI"])
        self.client.get(
            f"/api/search/projects/?q={query}",
            name="[Public] GET /api/search/projects/?q={term}"
        )

    @task(1)
    def google_oauth_init_login(self):
        """
        Simulate Google OAuth SSO initialization for login.
        """
        self.client.get(
            "/api/users/auth/google/?mode=login",
            name="[Public] GET /api/users/auth/google/?mode=login",
            allow_redirects=False,
        )

    @task(1)
    def google_oauth_init_register(self):
        """
        Simulate Google OAuth SSO initialization for registration.
        """
        self.client.get(
            "/api/users/auth/google/?mode=register",
            name="[Public] GET /api/users/auth/google/?mode=register",
            allow_redirects=False,
        )
