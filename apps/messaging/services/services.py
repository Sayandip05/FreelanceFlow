import logging
from typing import List

from django.db import transaction

from .models import Conversation, Message
from apps.bidding.models import Contract
from core.exceptions import ValidationError, PermissionDeniedError, NotFoundError

logger = logging.getLogger(__name__)


def get_or_create_conversation(contract_id: int) -> Conversation:
    """Get or create conversation for a contract."""
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        raise NotFoundError("Contract not found.")

    conversation, _ = Conversation.objects.get_or_create(contract=contract)
    return conversation


def send_message(sender, conversation_id: int, content: str) -> Message:
    """
    Persist a new message in a conversation.

    Uses select_related to pre-fetch contract → bid → freelancer/client in one
    query, avoiding lazy FK hits that would block the async event loop when
    this function is called via database_sync_to_async.
    """
    if not content or not content.strip():
        raise ValidationError("Message content is required.", field="content")

    try:
        conversation = (
            Conversation.objects
            .select_related(
                "contract__bid__freelancer",
                "contract__bid__project__client",
            )
            .get(id=conversation_id)
        )
    except Conversation.DoesNotExist:
        raise NotFoundError("Conversation not found.")

    contract = conversation.contract
    allowed_ids = {
        contract.bid.freelancer_id,
        contract.bid.project.client_id,
    }
    if sender.id not in allowed_ids:
        raise PermissionDeniedError("You are not a participant in this conversation.")

    with transaction.atomic():
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content.strip(),
        )
        conversation.save()  # bumps updated_at for conversation list ordering
        return message


def mark_messages_as_read(conversation_id: int, user) -> int:
    """
    Mark all unread messages (sent by the other party) as read.
    Returns the count of messages updated. Used by the REST endpoint.
    """
    return (
        Message.objects
        .filter(conversation_id=conversation_id, is_read=False)
        .exclude(sender=user)
        .update(is_read=True)
    )


def mark_messages_as_read_returning_ids(conversation_id: int, user) -> List[int]:
    """
    Mark all unread messages (sent by the other party) as read and return
    their IDs so the WebSocket consumer can broadcast the exact set of
    message IDs back to the sender's socket as a read receipt event.

    Fetches only PKs via .only("id") to avoid unnecessary column reads.
    Returns an empty list if nothing was unread (idempotent).
    """
    unread_qs = (
        Message.objects
        .filter(conversation_id=conversation_id, is_read=False)
        .exclude(sender=user)
        .only("id")
    )
    message_ids = list(unread_qs.values_list("id", flat=True))

    if message_ids:
        Message.objects.filter(id__in=message_ids).update(is_read=True)
        logger.debug(
            "Marked %d messages as read in conversation_id=%s for user_id=%s",
            len(message_ids), conversation_id, user.id,
        )

    return message_ids
