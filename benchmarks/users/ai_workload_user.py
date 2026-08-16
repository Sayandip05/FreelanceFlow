"""
AI / RAG Pipeline Workload User
Measures Qdrant vector memory retrieval and Groq LLaMA 3.3 70B (with Gemini fallback) inference latency.
"""
from locust import task, between
from benchmarks.config import TEST_USERS
from benchmarks.users.base_user import AuthenticatedHttpUser


class AIRagUser(AuthenticatedHttpUser):
    """
    Simulates AI Worklog Assistant usage and Qdrant vector context grounding.
    """
    weight = 1
    wait_time = between(3, 8)
    user_credentials = TEST_USERS["freelancer"]
    contract_id = 1

    def on_start(self):
        super().on_start()
        res = self.client.get("/api/bidding/contracts/")
        if res.status_code == 200:
            data = res.json()
            contracts = data.get("results", data if isinstance(data, list) else [])
            if contracts:
                self.contract_id = contracts[0]["id"]

    @task(3)
    def fetch_ai_context_and_vector_memory(self):
        """
        Fetch Qdrant vector memory grounding + contract context.
        """
        self.profile_request(
            "GET",
            f"/api/worklogs/ai/context/?contract_id={self.contract_id}",
            name="[AI/RAG] GET /api/worklogs/ai/context/?contract_id=:id"
        )

    @task(1)
    def invoke_ai_assistant_chat(self):
        """
        Invoke 3-node LangGraph AI assistant for worklog synthesis.
        """
        payload = {
            "contract_id": self.contract_id,
            "message": "Today I optimized PostgreSQL indexes and resolved N+1 query bottlenecks."
        }
        self.profile_request(
            "POST",
            "/api/worklogs/ai/chat/",
            json=payload,
            name="[AI/RAG] POST /api/worklogs/ai/chat/ (LangGraph + Groq/Gemini)"
        )
