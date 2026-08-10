from rest_framework import serializers
from apps.messaging.models import Conversation, Message
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
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id',
            'contract',
            'other_user',
            'last_message',
            'unread_count',
            'created_at',
            'updated_at',
        ]
    
    def get_other_user(self, obj):
        request = self.context.get('request')
        current_user = request.user if request and hasattr(request, 'user') else None
        contract = getattr(obj, 'contract', None)
        if not contract:
            return None
        freelancer = getattr(contract, 'freelancer', None)
        client = getattr(contract, 'client', None)
        if current_user and getattr(current_user, 'id', None) == getattr(freelancer, 'id', None):
            return UserSerializer(client).data if client else None
        return UserSerializer(freelancer).data if freelancer else None

    def get_last_message(self, obj):
        if hasattr(obj, 'prefetched_messages') and obj.prefetched_messages:
            return MessageSerializer(obj.prefetched_messages[0]).data
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
    
    def get_unread_count(self, obj):
        if hasattr(obj, 'annotated_unread_count'):
            return obj.annotated_unread_count
        request = self.context.get('request')
        user = request.user if request and hasattr(request, 'user') else None
        if not user or not user.is_authenticated:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=user).count()


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending messages."""
    content = serializers.CharField(required=True, min_length=1)
