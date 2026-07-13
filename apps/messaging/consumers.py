import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from .services import (
    get_or_create_conversation,
    mark_messages_as_read_returning_ids,
    send_message,
)

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Async WebSocket consumer for real-time contract chat.

    Authentication: JWT passed as ?token=<access_token> query parameter.
    Authorization:  Only the contract's client and freelancer may connect.

    Every Django ORM call is wrapped in database_sync_to_async because the
    Django ORM is fully synchronous — calling it directly inside an async
    method blocks the event loop and causes silent hangs under load.

    Read receipts
    ─────────────
    On connect:  all existing unread messages are marked read immediately
                 and a read_receipt event is broadcast to the room so the
                 sender's UI updates its tick marks right away.

    On receive:  when the other party is already online and sends a message,
                 the recipient marks it read in the same receive() call and
                 broadcasts the receipt — zero round-trip delay.

    Client-initiated: the frontend can send {"type": "read_receipt"} at any
                 time (e.g., when the user scrolls to the bottom or focuses
                 the window) to flush all unread messages for that session.

    Read receipt event shape (broadcast to room group):
    {
        "type": "read_receipt",
        "reader_id": <int>,
        "message_ids": [<int>, ...]   // exact IDs that were just marked read
    }
    """

    # ------------------------------------------------------------------ #
    # Connection lifecycle                                                 #
    # ------------------------------------------------------------------ #

    async def connect(self):
        self.contract_id: str = self.scope["url_route"]["kwargs"]["contract_id"]
        self.room_group_name: str = f"chat_{self.contract_id}"
        self.user = None
        self.conversation_id: int | None = None

        # Step 1 — Authenticate via JWT in query string
        self.user = await self._get_user_from_token()
        if isinstance(self.user, AnonymousUser):
            logger.warning(
                "WebSocket rejected: unauthenticated connection attempt "
                "for contract_id=%s", self.contract_id,
            )
            await self.close(code=4001)
            return

        # Step 2 — Authorise: only contract participants may join
        if not await self._is_contract_participant():
            logger.warning(
                "WebSocket rejected: user_id=%s is not a participant "
                "of contract_id=%s", self.user.id, self.contract_id,
            )
            await self.close(code=4003)
            return

        # Step 3 — Join the Redis channel group for this contract
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        logger.info(
            "WebSocket connected: user_id=%s joined group=%s",
            self.user.id, self.room_group_name,
        )

        # Step 4 — Mark existing unread messages as read on connect and
        #           broadcast the receipt so the sender's UI updates immediately.
        await self._flush_unread_and_broadcast()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name,
            )
        logger.info(
            "WebSocket disconnected: user_id=%s group=%s code=%s",
            getattr(self.user, "id", "anonymous"),
            getattr(self, "room_group_name", "unknown"),
            close_code,
        )

    # ------------------------------------------------------------------ #
    # Inbound message dispatch                                             #
    # ------------------------------------------------------------------ #

    async def receive(self, text_data: str):
        """
        Route inbound frames by their 'type' field:
          - (no type / "message") → send a chat message
          - "read_receipt"        → client-initiated receipt flush
        """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON payload.")
            return

        frame_type = data.get("type", "message")

        if frame_type == "read_receipt":
            await self._handle_read_receipt()
        else:
            await self._handle_chat_message(data)

    # ------------------------------------------------------------------ #
    # Chat message handler                                                 #
    # ------------------------------------------------------------------ #

    async def _handle_chat_message(self, data: dict):
        """Validate → persist → broadcast a new chat message."""
        message_content: str = data.get("message", "").strip()
        if not message_content:
            await self._send_error("Message content cannot be empty.")
            return

        try:
            # Resolve conversation (get_or_create — idempotent)
            conversation = await database_sync_to_async(
                get_or_create_conversation
            )(int(self.contract_id))

            # Cache conversation_id so _flush_unread_and_broadcast can reuse it
            self.conversation_id = conversation.id

            # Persist message
            message = await database_sync_to_async(send_message)(
                sender=self.user,
                conversation_id=conversation.id,
                content=message_content,
            )

            # Broadcast new message to all sockets in this room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": {
                        "id": message.id,
                        "content": message.content,
                        "sender": {
                            "id": self.user.id,
                            "email": self.user.email,
                            "full_name": self.user.get_full_name(),
                        },
                        "created_at": message.created_at.isoformat(),
                        "is_read": False,
                    },
                },
            )

            # If the other party is online they will receive this message in
            # their chat_message() handler and immediately send back a receipt.
            # If they are offline, the receipt arrives when they next connect.

        except Exception:
            logger.exception(
                "Error sending chat message: user_id=%s contract_id=%s",
                getattr(self.user, "id", None), self.contract_id,
            )
            await self._send_error("Failed to send message. Please try again.")

    # ------------------------------------------------------------------ #
    # Read receipt handler                                                 #
    # ------------------------------------------------------------------ #

    async def _handle_read_receipt(self):
        """
        Client-initiated receipt flush.
        The frontend sends {"type": "read_receipt"} when the user:
          - focuses the chat window
          - scrolls to the bottom
          - taps a 'Mark all read' button
        """
        await self._flush_unread_and_broadcast()

    async def _flush_unread_and_broadcast(self):
        """
        Core read-receipt logic:
          1. Mark all unread messages (sent by the other party) as read in DB.
          2. If any were updated, broadcast a read_receipt event to the whole
             room group so the sender's open socket sees the update instantly.

        No-ops silently if conversation_id is not yet known (e.g., first ever
        connect before any messages exist) or if nothing was unread.
        """
        # Resolve conversation_id if not cached yet
        if not self.conversation_id:
            try:
                conversation = await database_sync_to_async(
                    get_or_create_conversation
                )(int(self.contract_id))
                self.conversation_id = conversation.id
            except Exception:
                logger.debug(
                    "Could not resolve conversation on connect for contract_id=%s",
                    self.contract_id,
                )
                return

        try:
            message_ids = await database_sync_to_async(
                mark_messages_as_read_returning_ids
            )(self.conversation_id, self.user)

            if not message_ids:
                return  # nothing to broadcast

            # Broadcast to the whole room so the original sender's socket
            # can update its tick marks (✓ → ✓✓ blue style)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "read_receipt",
                    "reader_id": self.user.id,
                    "message_ids": message_ids,
                },
            )

            logger.debug(
                "Read receipt broadcast: reader_id=%s message_ids=%s",
                self.user.id, message_ids,
            )

        except Exception:
            logger.exception(
                "Error processing read receipt: user_id=%s conversation_id=%s",
                getattr(self.user, "id", None), self.conversation_id,
            )

    # ------------------------------------------------------------------ #
    # Channel layer event handlers (called by group_send → deliver)       #
    # ------------------------------------------------------------------ #

    async def chat_message(self, event: dict):
        """
        Deliver a new chat message to this specific WebSocket connection.
        After delivering, immediately mark it as read (if we are the recipient)
        and broadcast the receipt — so the sender sees read ticks with no
        extra round-trip from the frontend.
        """
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            **event["message"],
        }))

        # Auto-receipt: if I am NOT the sender, mark it read immediately
        sender_id = event["message"]["sender"]["id"]
        if self.user.id != sender_id:
            await self._flush_unread_and_broadcast()

    async def read_receipt(self, event: dict):
        """
        Deliver a read receipt event to this specific WebSocket connection.
        The frontend uses this to update message tick marks.

        Payload delivered to the browser:
        {
            "type": "read_receipt",
            "reader_id": <int>,
            "message_ids": [<int>, ...]
        }
        """
        await self.send(text_data=json.dumps(event))

    # ------------------------------------------------------------------ #
    # Private ORM helpers — all wrapped with @database_sync_to_async      #
    # ------------------------------------------------------------------ #

    @database_sync_to_async
    def _get_user_from_token(self):
        """
        Parse the JWT from ?token=<value> in the WebSocket URL and return the
        corresponding User instance with select_related pre-loaded so that
        attribute access inside async methods (id, email, get_full_name)
        does NOT trigger additional synchronous DB queries.

        Returns AnonymousUser on any auth failure.
        """
        from apps.users.models import User  # local import avoids circular deps

        query_string: str = self.scope.get("query_string", b"").decode()
        if "token=" not in query_string:
            return AnonymousUser()

        raw_token = query_string.split("token=")[1].split("&")[0]
        if not raw_token:
            return AnonymousUser()

        try:
            access_token = AccessToken(raw_token)
            user_id = access_token["user_id"]
            return (
                User.objects
                .select_related("freelancer_profile", "client_profile")
                .get(id=user_id)
            )
        except Exception as exc:
            logger.debug("WebSocket JWT validation failed: %s", exc)
            return AnonymousUser()

    @database_sync_to_async
    def _is_contract_participant(self) -> bool:
        """
        Verify that self.user is either the client or the freelancer on the
        contract identified by self.contract_id.

        select_related pre-fetches bid → freelancer and bid → project → client
        in a single JOIN query, avoiding implicit lazy DB hits.
        """
        from apps.bidding.models import Contract  # local import avoids circular deps

        try:
            contract = (
                Contract.objects
                .select_related("bid__freelancer", "bid__project__client")
                .get(id=self.contract_id)
            )
            allowed_ids = {
                contract.bid.freelancer_id,
                contract.bid.project.client_id,
            }
            return self.user.id in allowed_ids
        except Contract.DoesNotExist:
            return False

    # ------------------------------------------------------------------ #
    # Utility                                                              #
    # ------------------------------------------------------------------ #

    async def _send_error(self, message: str):
        """Send a structured error payload to the connected client."""
        await self.send(text_data=json.dumps({"type": "error", "error": message}))
