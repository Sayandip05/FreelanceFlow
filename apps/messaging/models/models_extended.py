"""Extended messaging models - Search, Typing Indicators."""
from django.db import models
from apps.users.models import User
from .models import Conversation


class MessageSearch(models.Model):
    """
    Indexed message content for search.
    """
    message = models.OneToOneField(
        'messaging.Message',
        on_delete=models.CASCADE,
        related_name="search_index"
    )
    content_vector = models.TextField()  # For full-text search
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "message_search"
        indexes = [
            models.Index(fields=["content_vector"]),
        ]


class TypingIndicator(models.Model):
    """
    Real-time typing indicators.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="typing_indicators"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    is_typing = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "typing_indicators"
        unique_together = ["conversation", "user"]
    
    def __str__(self):
        return f"{self.user.email} typing in {self.conversation.id}"
