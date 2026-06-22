"""
Typing Indicator Services
"""
from django.db import transaction
from .models_extended import TypingIndicator


@transaction.atomic
def set_typing(conversation_id, user, is_typing=True):
    """Set typing indicator"""
    indicator, created = TypingIndicator.objects.update_or_create(
        conversation_id=conversation_id,
        user=user,
        defaults={'is_typing': is_typing}
    )
    return indicator


def get_typing_users(conversation_id):
    """Get users currently typing"""
    return TypingIndicator.objects.filter(
        conversation_id=conversation_id,
        is_typing=True
    ).select_related('user')
