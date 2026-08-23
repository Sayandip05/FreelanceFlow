import json
import logging
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


# ─── Channel-layer helper for project bid events ──────────────────────────────
def push_project_event(project_id: int, event_type: str, payload: dict):
    """
    Broadcasts a project-related event (like new bid submissions) to the project group.
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("No channel layer — skipping project event push project_id=%s", project_id)
        return

    group_name = f"project_{project_id}"
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "project.event",
                "event_type": event_type,
                "payload": payload,
            },
        )
        logger.debug("Project event pushed: group=%s event=%s", group_name, event_type)
    except Exception as exc:
        logger.warning("Failed to push project event project_id=%s: %s", project_id, exc)


# ─── Project Consumer ─────────────────────────────────────────────────────────
class ProjectConsumer(AsyncWebsocketConsumer):
    """
    WebSocket channel for project real-time events (bids, updates).
    URL: ws/project/<project_id>/?token=<token>
    """

    async def connect(self):
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.group_name = f"project_{self.project_id}"
        self.user = None

        await self.accept()

        # Authenticate
        self.user = await self._get_user_from_token()
        if not self.user or isinstance(self.user, AnonymousUser):
            await self._send_error("Authentication required")
            await self.close(code=4001)
            return

        # Authorise: verify user is project owner (client) or bidding (freelancer)
        if not await self._has_project_access():
            await self._send_error("Permission denied")
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        logger.info("ProjectConsumer connected: user_id=%s project_id=%s", self.user.id, self.project_id)

        await self.send(text_data=json.dumps({
            "type": "connected",
            "project_id": self.project_id,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name") and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info("ProjectConsumer disconnected: user_id=%s code=%s", getattr(self.user, "id", "anon"), close_code)

    async def receive(self, text_data: str):
        # We only receive events in contract drafting, not project views
        pass

    async def project_event(self, event: dict):
        await self.send(text_data=json.dumps({
            "type": event["event_type"],
            "payload": event["payload"],
        }))

    @database_sync_to_async
    def _has_project_access(self) -> bool:
        from apps.projects.models import Project
        try:
            project = Project.objects.get(id=self.project_id)
            # Owner has access
            if project.client_id == self.user.id:
                return True
            # Freelancers can access only if they have bid or can bid
            return self.user.role == "FREELANCER"
        except Exception:
            return False

    @database_sync_to_async
    def _get_user_from_token(self):
        import urllib.parse
        from rest_framework_simplejwt.tokens import AccessToken
        from apps.users.models import User

        query_string = self.scope.get("query_string", b"").decode()
        params = urllib.parse.parse_qs(query_string)
        raw_token = params.get("token", [None])[0]

        if not raw_token:
            headers = dict(self.scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.startswith("Bearer "):
                raw_token = auth_header.split("Bearer ")[1]

        if not raw_token:
            return AnonymousUser()

        try:
            access_token = AccessToken(raw_token)
            return User.objects.get(id=access_token["user_id"])
        except Exception:
            return AnonymousUser()

    async def _send_error(self, message: str):
        await self.send(text_data=json.dumps({"type": "error", "error": message}))


# ─── Contract Draft Consumer ──────────────────────────────────────────────────
class ContractDraftConsumer(AsyncWebsocketConsumer):
    """
    WebSocket channel for collaborative milestone schedule drafting.
    URL: ws/contract-draft/<contract_id>/?token=<token>
    """

    async def connect(self):
        self.contract_id = self.scope["url_route"]["kwargs"]["contract_id"]
        self.group_name = f"contract_draft_{self.contract_id}"
        self.user = None

        await self.accept()

        self.user = await self._get_user_from_token()
        if not self.user or isinstance(self.user, AnonymousUser):
            await self._send_error("Authentication required")
            await self.close(code=4001)
            return

        if not await self._is_contract_participant():
            await self._send_error("Permission denied")
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        logger.info("ContractDraftConsumer connected: user_id=%s contract_id=%s", self.user.id, self.contract_id)

        await self.send(text_data=json.dumps({
            "type": "connected",
            "contract_id": self.contract_id,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name") and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info("ContractDraftConsumer disconnected: user_id=%s code=%s", getattr(self.user, "id", "anon"), close_code)

    async def receive(self, text_data: str):
        try:
            data = json.loads(text_data)
            # Only Client can push draft edits
            if self.user.role != "CLIENT":
                return

            if data.get("type") == "draft_update":
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "draft.event",
                        "event_type": "draft_update",
                        "payload": data.get("milestones", []),
                    }
                )
        except Exception as e:
            logger.error("Error receiving draft WS payload: %s", e)

    async def draft_event(self, event: dict):
        await self.send(text_data=json.dumps({
            "type": event["event_type"],
            "payload": event["payload"],
        }))

    @database_sync_to_async
    def _is_contract_participant(self) -> bool:
        from apps.bidding.models import Contract
        try:
            contract = Contract.objects.select_related("bid__freelancer", "bid__project__client").get(id=self.contract_id)
            return self.user.id in {contract.bid.freelancer_id, contract.bid.project.client_id}
        except Exception:
            return False

    @database_sync_to_async
    def _get_user_from_token(self):
        import urllib.parse
        from rest_framework_simplejwt.tokens import AccessToken
        from apps.users.models import User

        query_string = self.scope.get("query_string", b"").decode()
        params = urllib.parse.parse_qs(query_string)
        raw_token = params.get("token", [None])[0]

        if not raw_token:
            return AnonymousUser()

        try:
            access_token = AccessToken(raw_token)
            return User.objects.get(id=access_token["user_id"])
        except Exception:
            return AnonymousUser()

    async def _send_error(self, message: str):
        await self.send(text_data=json.dumps({"type": "error", "error": message}))
