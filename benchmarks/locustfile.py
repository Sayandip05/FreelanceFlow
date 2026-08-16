"""
Master Locustfile for FreelanceFlow
Orchestrates multi-persona load tests across HTTP REST, WebSockets, and AI pipelines.
"""
from benchmarks.users.freelancer_user import FreelancerUser
from benchmarks.users.client_user import ClientUser
from benchmarks.users.unauthenticated_user import PublicUser
from benchmarks.users.websocket_user import WebSocketChatUser
from benchmarks.users.ai_workload_user import AIRagUser

__all__ = [
    "FreelancerUser",
    "ClientUser",
    "PublicUser",
    "WebSocketChatUser",
    "AIRagUser",
]
