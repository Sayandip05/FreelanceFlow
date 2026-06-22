from django.db import models
from django.conf import settings

from apps.bidding.models import Contract


class Conversation(models.Model):
    """
    One conversation per contract between client and freelancer.
    """
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name="conversation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "conversations"
        ordering = ["-updated_at"]
    
    def __str__(self):
        return f"Conversation for {self.contract.bid.project.title}"


class Message(models.Model):
    """
    Individual messages in a conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    content = models.TextField()
    
    # Attachments
    attachments = models.JSONField(
        default=list,
        blank=True,
        help_text="List of attachment URLs with metadata"
    )
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "messages"
        ordering = ["created_at"]
    
    def __str__(self):
        return f"Message from {self.sender.email} at {self.created_at}"
