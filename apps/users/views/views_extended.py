"""
Views for Extended User Features
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from apps.users.serializers.serializers_extended import (
    ActivityLogSerializer, ActivitySummarySerializer,
    UserOnlineStatusSerializer, UpdateStatusMessageSerializer,
    OnlineUsersSerializer
)
from apps.users.services.services_activity import (
    get_user_activity_log, get_recent_logins,
    get_security_events, get_activity_summary
)
from apps.users.services.services_status import (
    get_user_status, set_status_message, clear_status_message,
    get_online_users, get_online_count, is_user_online
)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Activity Logs (Read-only)
    
    Endpoints:
    - GET /api/users/activity/ - List activity logs
    - GET /api/users/activity/security/ - Security events
    - GET /api/users/activity/summary/ - Activity summary
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ActivityLogSerializer
    
    def get_queryset(self):
        """Get activity logs for current user"""
        return get_user_activity_log(self.request.user, limit=100)
    
    @action(detail=False, methods=['get'])
    def security(self, request):
        """Get security-related events"""
        events = get_security_events(request.user, limit=50)
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get activity summary"""
        days = int(request.query_params.get('days', 30))
        summary = get_activity_summary(request.user, days=days)
        
        # Convert dict to list of objects
        summary_list = [
            {'action': action, 'count': count}
            for action, count in summary.items()
        ]
        
        serializer = ActivitySummarySerializer(summary_list, many=True)
        return Response(serializer.data)


class OnlineStatusViewSet(viewsets.ViewSet):
    """
    ViewSet for Online Status
    
    Endpoints:
    - GET /api/users/status/me/ - Get my status
    - POST /api/users/status/message/ - Update status message
    - DELETE /api/users/status/message/ - Clear status message
    - GET /api/users/status/online/ - Get online users
    - GET /api/users/status/count/ - Get online count
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's status"""
        status_data = get_user_status(request.user)
        return Response(status_data)
    
    @action(detail=False, methods=['post'])
    def message(self, request):
        """Update status message"""
        serializer = UpdateStatusMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.validated_data.get('status_message', '')
        
        if message:
            set_status_message(request.user, message)
        else:
            clear_status_message(request.user)
        
        return Response({
            'message': 'Status message updated',
            'status_message': message
        })
    
    @action(detail=False, methods=['delete'])
    def message(self, request):
        """Clear status message"""
        clear_status_message(request.user)
        return Response({
            'message': 'Status message cleared'
        })
    
    @action(detail=False, methods=['get'])
    def online(self, request):
        """Get list of online users"""
        limit = int(request.query_params.get('limit', 50))
        online_users = get_online_users(limit=limit)
        
        data = []
        for user in online_users:
            data.append({
                'user_id': user.id,
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}".strip() or user.email,
                'is_online': is_user_online(user),
                'last_seen': get_user_status(user)['last_seen']
            })
        
        serializer = OnlineUsersSerializer(data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        """Get count of online users"""
        count = get_online_count()
        return Response({
            'online_count': count
        })
