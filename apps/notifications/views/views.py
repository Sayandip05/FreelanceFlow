from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.notifications.models import Notification
from apps.notifications.selectors import (
    get_user_notifications,
    get_unread_notifications,
    get_unread_count
)
from apps.notifications.services import (
    mark_notification_as_read,
    mark_all_as_read,
    delete_notification
)
from apps.notifications.serializers import NotificationSerializer, NotificationMarkReadSerializer
from core.pagination import StandardResultsPagination


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing user notifications.
    
    list: Get all notifications for the authenticated user
    retrieve: Get a specific notification
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination
    
    def get_queryset(self):
        return get_user_notifications(self.request.user)
    
    @action(detail=False, methods=["get"])
    def unread(self, request):
        """Get unread notifications for the authenticated user."""
        notifications = get_unread_notifications(request.user)
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = get_unread_count(request.user)
        return Response({"unread_count": count})
    
    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark a specific notification as read."""
        notification = mark_notification_as_read(int(pk), request.user)
        if notification:
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
        return Response(
            {"detail": "Notification not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        count = mark_all_as_read(request.user)
        return Response({"marked_as_read": count})
    
    @action(detail=True, methods=["delete"])
    def delete(self, request, pk=None):
        """Delete a specific notification."""
        deleted = delete_notification(int(pk), request.user)
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Notification not found."},
            status=status.HTTP_404_NOT_FOUND
        )
