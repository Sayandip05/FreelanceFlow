"""
NotificationConsumer — Real-time notification push over WebSocket.

Each authenticated user joins their own private group:  notifications_<user_id>

On connect:
  - JWT is read from ?token= query param (same pattern as ChatConsumer)
  - User joins their personal group
  - Last 15 unread notifications are delivered immediately as an initial burst

On incoming WS message:
  - {"type": "mark_read", "id": <int>}  — marks a single notification as read

Channel-layer push:
  - Any code that calls push_notification_to_user(user_id, notification) will
    broadcast to this consumer in real-time.
"""
import json
import logging

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


# ─── Channel-layer helper (called from sync service code) ─────────────────────
def push_notification_to_user(user_id: int, notification_data: dict):
    """
    Synchronous helper: push a notification dict to a user's open browser tab.
    Called from create_notification() inside apps/notifications/services.

    notification_data must be a plain dict (JSON-serialisable):
      {
        "id": int,
        "title": str,
        "body": str,
        "type": str,
        "is_read": bool,
        "created_at": str (ISO-8601),
      }
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("No channel layer configured — skipping push for user_id=%s", user_id)
        return

    group_name = f"notifications_{user_id}"
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notify.new",
                "notification": notification_data,
            },
        )
        logger.debug("Pushed notification to group=%s notification_id=%s", group_name, notification_data.get("id"))
    except Exception as exc:
        logger.warning("Failed to push WS notification to user_id=%s: %s", user_id, exc)


# ─── Consumer ─────────────────────────────────────────────────────────────────
class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Per-user private WebSocket channel for real-time notifications.
    URL: ws/notifications/?token=<access_token>
    """

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def connect(self):
        self.user = None
        self.group_name = None

        await self.accept()

        # Authenticate
        self.user = await self._get_user_from_token()
        if not self.user or isinstance(self.user, AnonymousUser):
            await self._send_error("Authentication required")
            await self.close(code=4001)
            return

        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        logger.info("NotificationConsumer connected: user_id=%s group=%s", self.user.id, self.group_name)

        # Track online presence
        from django.core.cache import cache
        from asgiref.sync import sync_to_async
        presence_key = f"presence_count_user_{self.user.id}"
        
        @sync_to_async
        def track_presence():
            try:
                cache.add(presence_key, 0, timeout=None)
                cache.incr(presence_key)
            except Exception as e:
                logger.warning("Failed to increment presence counter: %s", e)
        
        await track_presence()

        # Deliver existing unread notifications immediately on connect
        await self._send_initial_notifications()

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            
            # Untrack online presence
            from django.core.cache import cache
            from asgiref.sync import sync_to_async
            if self.user and not isinstance(self.user, AnonymousUser):
                presence_key = f"presence_count_user_{self.user.id}"
                
                @sync_to_async
                def untrack_presence():
                    try:
                        current_count = cache.get(presence_key, 0)
                        if current_count > 0:
                            cache.decr(presence_key)
                    except Exception as e:
                        logger.warning("Failed to decrement presence counter: %s", e)
                
                await untrack_presence()

        logger.info(
            "NotificationConsumer disconnected: user_id=%s code=%s",
            getattr(self.user, "id", "anon"), close_code,
        )

    # ── Inbound frames ────────────────────────────────────────────────────────

    async def receive(self, text_data: str):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON")
            return

        frame_type = data.get("type", "")

        if frame_type == "mark_read":
            notif_id = data.get("id")
            if notif_id:
                await self._mark_read(notif_id)
        elif frame_type == "mark_all_read":
            await self._mark_all_read()

    # ── Channel-layer event handlers ──────────────────────────────────────────

    async def notify_new(self, event: dict):
        """
        Deliver a new notification pushed by push_notification_to_user().
        Frame type from group_send uses dot-notation; channels maps it to
        the method with underscores: notify.new → notify_new.
        """
        await self.send(text_data=json.dumps({
            "type": "new_notification",
            "notification": event["notification"],
        }))

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _send_initial_notifications(self):
        """Push last 15 unread notifications on connect."""
        try:
            notifications = await self._fetch_recent_unread()
            if notifications:
                await self.send(text_data=json.dumps({
                    "type": "initial_notifications",
                    "notifications": notifications,
                }))
        except Exception:
            logger.exception("Failed to send initial notifications for user_id=%s", getattr(self.user, "id", None))

    @database_sync_to_async
    def _fetch_recent_unread(self):
        from apps.notifications.models import Notification
        qs = (
            Notification.objects
            .filter(recipient=self.user, is_read=False)
            .order_by("-created_at")[:15]
        )
        return [
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "type": n.type,
                "action_url": n.action_url,
                "data": n.data,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in qs
        ]

    @database_sync_to_async
    def _mark_read(self, notification_id: int):
        from apps.notifications.models import Notification
        Notification.objects.filter(id=notification_id, recipient=self.user).update(is_read=True)

    @database_sync_to_async
    def _mark_all_read(self):
        from apps.notifications.models import Notification
        Notification.objects.filter(recipient=self.user, is_read=False).update(is_read=True)

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
            user_id = access_token["user_id"]
            return User.objects.get(id=user_id)
        except Exception as exc:
            logger.debug("NotificationConsumer JWT validation failed: %s", exc)
            return AnonymousUser()

    async def _send_error(self, message: str):
        await self.send(text_data=json.dumps({"type": "error", "error": message}))
