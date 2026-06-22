from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    SendMessageSerializer,
)
from .services import (
    get_or_create_conversation,
    send_message,
    mark_messages_as_read,
)
from .selectors import (
    get_user_conversations,
    get_conversation_messages,
    get_conversation_by_contract,
)
from core.exceptions import ValidationError
from core.pagination import StandardResultsPagination


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Conversation operations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsPagination
    
    def get_queryset(self):
        return get_user_conversations(self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get messages for a conversation."""
        conversation = self.get_object()
        messages = get_conversation_messages(conversation.id)
        
        # Apply pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send a message in a conversation."""
        conversation = self.get_object()
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            message = send_message(
                sender=request.user,
                conversation_id=conversation.id,
                content=serializer.validated_data['content'],
            )
            
            return Response(
                MessageSerializer(message).data,
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark all messages as read."""
        conversation = self.get_object()
        count = mark_messages_as_read(conversation.id, request.user)
        
        return Response(
            {"message": f"{count} messages marked as read."},
            status=status.HTTP_200_OK,
        )


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Message operations (read-only).
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsPagination
    
    def get_queryset(self):
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            return Message.objects.filter(
                conversation_id=conversation_id,
                conversation__in=get_user_conversations(self.request.user),
            ).select_related('sender').order_by('-created_at')[:50]
        return Message.objects.none()
