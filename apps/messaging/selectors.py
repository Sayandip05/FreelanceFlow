from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from .models import Conversation, Message


def get_conversation_by_id(conversation_id: int) -> Conversation:
    """Get conversation by ID."""
    return get_object_or_404(Conversation, id=conversation_id)


def get_conversation_by_contract(contract_id: int) -> Conversation | None:
    """Get conversation for a contract."""
    try:
        return Conversation.objects.get(contract_id=contract_id)
    except Conversation.DoesNotExist:
        return None


def get_user_conversations(user) -> QuerySet[Conversation]:
    """Get all conversations for a user."""
    return Conversation.objects.filter(
        contract__bid__freelancer=user
    ) | Conversation.objects.filter(
        contract__bid__project__client=user
    )


def get_conversation_messages(
    conversation_id: int,
    limit: int = 50
) -> QuerySet[Message]:
    """Get messages for a conversation."""
    return Message.objects.filter(
        conversation_id=conversation_id
    ).select_related('sender').order_by('-created_at')[:limit]


def get_unread_messages_count(user) -> int:
    """Get count of unread messages for a user."""
    return Message.objects.filter(
        conversation__in=get_user_conversations(user),
        is_read=False
    ).exclude(sender=user).count()
