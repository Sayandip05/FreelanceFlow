from django.contrib import admin
from apps.messaging.models import Conversation, Message


class MessageInline(admin.TabularInline):
    """Inline admin for messages in a conversation."""
    model = Message
    extra = 0
    readonly_fields = ["created_at"]
    fields = ["sender", "content", "is_read", "created_at"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin configuration for Conversation model."""
    
    list_display = [
        "id",
        "contract",
        "created_at",
        "updated_at",
        "message_count"
    ]
    search_fields = [
        "contract__bid__project__title",
        "contract__bid__freelancer__email"
    ]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [MessageInline]
    
    def message_count(self, obj):
        """Display number of messages in conversation."""
        return obj.messages.count()
    message_count.short_description = "Messages"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for Message model."""
    
    list_display = [
        "id",
        "conversation",
        "sender",
        "content_preview",
        "is_read",
        "created_at"
    ]
    list_filter = ["is_read", "created_at"]
    search_fields = ["content", "sender__email"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
    
    def content_preview(self, obj):
        """Display truncated message content."""
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content"
