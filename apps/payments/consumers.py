"""
ContractConsumer — Real-time contract & milestone status updates over WebSocket.

Both contract participants (client + freelancer) join:  contract_<contract_id>

Events broadcast to this group (from services_milestone.py):
  - milestone_funded      — client funded a milestone (IN_PROGRESS)
  - milestone_submitted   — freelancer submitted deliverables
  - milestone_approved    — client approved and released payment
  - milestone_rejected    — client requested revision (back to IN_PROGRESS)

Frontend receives these events and triggers a REST re-fetch to stay in sync.
"""
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


# ─── Channel-layer helper (called from sync service code) ─────────────────────
def push_contract_event(contract_id: int, event_type: str, payload: dict):
    """
    Synchronous helper: broadcast a contract event to all participants
    currently viewing this contract's detail page.

    Args:
        contract_id: The contract primary key
        event_type:  One of milestone_funded, milestone_submitted,
                     milestone_approved, milestone_rejected
        payload:     Extra data dict (milestone_id, new_status, etc.)
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("No channel layer — skipping contract event push contract_id=%s", contract_id)
        return

    group_name = f"contract_{contract_id}"
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "contract.event",
                "event_type": event_type,
                "payload": payload,
            },
        )
        logger.debug("Contract event pushed: group=%s event=%s", group_name, event_type)
    except Exception as exc:
        logger.warning("Failed to push contract event contract_id=%s: %s", contract_id, exc)


# ─── Consumer ─────────────────────────────────────────────────────────────────
class ContractConsumer(AsyncWebsocketConsumer):
    """
    Per-contract WebSocket channel for milestone status push.
    URL: ws/contract/<contract_id>/?token=<access_token>
    """

    async def connect(self):
        self.contract_id = self.scope["url_route"]["kwargs"]["contract_id"]
        self.group_name = f"contract_{self.contract_id}"
        self.user = None

        await self.accept()

        # Authenticate
        self.user = await self._get_user_from_token()
        if not self.user or isinstance(self.user, AnonymousUser):
            await self._send_error("Authentication required")
            await self.close(code=4001)
            return

        # Authorise — only contract participants may subscribe
        if not await self._is_contract_participant():
            await self._send_error("Permission denied: not a contract participant")
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        logger.info(
            "ContractConsumer connected: user_id=%s contract_id=%s",
            self.user.id, self.contract_id,
        )

        # Acknowledge connection
        await self.send(text_data=json.dumps({
            "type": "connected",
            "contract_id": self.contract_id,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name") and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(
            "ContractConsumer disconnected: user_id=%s contract_id=%s code=%s",
            getattr(self.user, "id", "anon"), self.contract_id, close_code,
        )

    async def receive(self, text_data: str):
        # Clients don't send anything meaningful — ignore inbound frames
        pass

    # ── Channel-layer event handler ───────────────────────────────────────────

    async def contract_event(self, event: dict):
        """
        Forward a contract event to this specific WebSocket connection.
        group_send type 'contract.event' → channels calls 'contract_event'.
        """
        await self.send(text_data=json.dumps({
            "type": event["event_type"],
            "payload": event["payload"],
        }))

    # ── Helpers ───────────────────────────────────────────────────────────────

    @database_sync_to_async
    def _is_contract_participant(self) -> bool:
        from apps.bidding.models import Contract
        try:
            contract = (
                Contract.objects
                .select_related("bid__freelancer", "bid__project__client")
                .get(id=self.contract_id)
            )
            allowed = {contract.bid.freelancer_id, contract.bid.project.client_id}
            return self.user.id in allowed
        except Exception as exc:
            logger.debug("ContractConsumer participant check failed: %s", exc)
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
        except Exception as exc:
            logger.debug("ContractConsumer JWT validation failed: %s", exc)
            return AnonymousUser()

    async def _send_error(self, message: str):
        await self.send(text_data=json.dumps({"type": "error", "error": message}))
