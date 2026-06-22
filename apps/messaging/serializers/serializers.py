from rest_framework import serializers

from .models import Conversation, Message
from apps.users.serializers import UserSerializer
from apps.bidding.serializers import ContractSerializer


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages."""
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'content',
            'is_read',
            'created_at',
        ]


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversations."""
    contract = ContractSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id',
            'contract',
            'last_message',
            'unread_count',
            'created_at',
            'updated_at',
        ]
    
    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
    
    def get_unread_count(self, obj):
        user = self.context.get('request').user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending messages."""
    content = serializers.CharField(required=True, min_length=1)
