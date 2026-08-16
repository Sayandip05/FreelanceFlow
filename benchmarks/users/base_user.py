"""
Base Authenticated Locust User
Handles JWT authentication, token lifecycle, and server-side SQL profiling capture.
"""
import logging
from collections import defaultdict
from locust import HttpUser, events

logger = logging.getLogger(__name__)

# Global thread-safe store for server-side SQL metrics captured via response headers
DB_METRICS_STORE = defaultdict(lambda: {
    "total_requests": 0,
    "total_queries": 0,
    "total_query_time_ms": 0.0,
    "duplicate_queries": 0,
    "slow_queries": 0,
    "max_queries": 0,
})


class AuthenticatedHttpUser(HttpUser):
    """
    Base user that authenticates via JWT and captures database query telemetry.
    """
    abstract = True
    user_credentials = None
    access_token = None
    refresh_token = None
    user_id = None
    role = None

    def on_start(self):
        """
        Authenticate with backend on user spawn.
        """
        self.authenticate()

    def authenticate(self):
        """
        Log in with user credentials and obtain JWT access + refresh tokens with retry backoff.
        """
        if not self.user_credentials:
            return

        payload = {
            "email": self.user_credentials["email"],
            "password": self.user_credentials["password"],
        }

        for attempt in range(3):
            with self.client.post(
                "/api/users/login/",
                json=payload,
                name="[Auth] POST /api/users/login/",
                catch_response=True,
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access") or data.get("access_token") or data.get("tokens", {}).get("access")
                    self.refresh_token = data.get("refresh") or data.get("refresh_token") or data.get("tokens", {}).get("refresh")
                    self.user_id = data.get("user", {}).get("id")
                    self.role = data.get("user", {}).get("role")

                    # Configure authenticated headers with SQL profiling enabled
                    self.client.headers.update({
                        "Authorization": f"Bearer {self.access_token}",
                        "X-Benchmark-Profile": "true",
                    })
                    response.success()
                    return
                else:
                    if attempt == 2:
                        logger.warning(
                            f"Authentication failed for {self.user_credentials['email']} (status {response.status_code}): {response.text}"
                        )
                        response.failure(f"Login failed: {response.status_code}")
                    time.sleep(0.5)


    def profile_request(self, method: str, url: str, name: str = None, **kwargs):
        """
        Wrapper around client requests that captures server-side database profiling headers.
        """
        endpoint_name = name or f"[{method.upper()}] {url}"
        response = self.client.request(method, url, name=endpoint_name, **kwargs)

        # Extract profiling headers added by PerformanceProfilingMiddleware
        query_count = int(response.headers.get("X-DB-Query-Count", 0))
        query_time = float(response.headers.get("X-DB-Query-Time-Ms", 0.0))
        duplicate_queries = int(response.headers.get("X-DB-Duplicate-Queries", 0))
        slow_queries = int(response.headers.get("X-DB-Slow-Queries", 0))

        if query_count > 0:
            stats = DB_METRICS_STORE[endpoint_name]
            stats["total_requests"] += 1
            stats["total_queries"] += query_count
            stats["total_query_time_ms"] += query_time
            stats["duplicate_queries"] += duplicate_queries
            stats["slow_queries"] += slow_queries
            stats["max_queries"] = max(stats["max_queries"], query_count)

        return response
