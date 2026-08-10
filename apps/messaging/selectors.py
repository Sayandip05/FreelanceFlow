from django.db.models import QuerySet, Count, Q, Prefetch
from django.shortcuts import get_object_or_404
from .models import Conversation, Message


def get_conversation_by_id(conversation_id: int) -> Conversation:
    """Get conversation by ID."""
    return get_object_or_404(
        Conversation.objects.select_related(
            'contract',
            'contract__bid__project',
            'contract__bid__project__client',
            'contract__bid__project__client__client_profile',
            'contract__bid__project__client__freelancer_profile',
            'contract__bid__freelancer',
            'contract__bid__freelancer__freelancer_profile',
            'contract__bid__freelancer__client_profile',
        ),
        id=conversation_id
    )


def get_conversation_by_contract(contract_id: int) -> Conversation | None:
    """Get conversation for a contract."""
    try:
        return Conversation.objects.select_related(
            'contract',
            'contract__bid__project',
            'contract__bid__project__client',
            'contract__bid__freelancer',
        ).get(contract_id=contract_id)
    except Conversation.DoesNotExist:
        return None


def get_user_conversations(user) -> QuerySet[Conversation]:
    """Get all conversations for a user, ensuring active contracts have a conversation record."""
    from apps.bidding.models import Contract
    missing_contracts = Contract.objects.filter(
        Q(bid__freelancer=user) | Q(bid__project__client=user)
    ).filter(conversation__isnull=True)
    for c in missing_contracts:
        Conversation.objects.get_or_create(contract=c)

    return Conversation.objects.filter(
        Q(contract__bid__freelancer=user) | Q(contract__bid__project__client=user)
    ).select_related(
        'contract',
        'contract__bid__project',
        'contract__bid__project__client',
        'contract__bid__project__client__client_profile',
        'contract__bid__project__client__freelancer_profile',
        'contract__bid__freelancer',
        'contract__bid__freelancer__freelancer_profile',
        'contract__bid__freelancer__client_profile',
    ).annotate(
        annotated_unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=user)
        )
    ).prefetch_related(
        Prefetch(
            'messages',
            queryset=Message.objects.select_related(
                'sender',
                'sender__freelancer_profile',
                'sender__client_profile'
            ).order_by('-created_at'),
            to_attr='prefetched_messages'
        )
    ).order_by('-updated_at')


def get_conversation_messages(
    conversation_id: int,
    limit: int | None = None
) -> QuerySet[Message]:
    """Get messages for a conversation ordered by newest first."""
    qs = Message.objects.filter(
        conversation_id=conversation_id
    ).select_related(
        'sender',
        'sender__freelancer_profile',
        'sender__client_profile'
    ).order_by('-created_at')
    if limit is not None:
        return qs[:limit]
    return qs


def get_unread_messages_count(user) -> int:
    """Get count of unread messages for a user."""
    return Message.objects.filter(
        conversation__in=get_user_conversations(user),
        is_read=False
    ).exclude(sender=user).count()
