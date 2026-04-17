"""
Views for Extended User Features
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from .serializers_extended import (
    Enable2FASerializer, Verify2FASerializer, Disable2FASerializer,
    TwoFactorAuthStatusSerializer, Enable2FAResponseSerializer,
    ActivityLogSerializer, ActivitySummarySerializer,
    UserOnlineStatusSerializer, UpdateStatusMessageSerializer,
    OnlineUsersSerializer
)
from .services_2fa import (
    enable_2fa, verify_and_enable_2fa, verify_2fa_code,
    disable_2fa, is_2fa_enabled, regenerate_backup_codes
)
from .services_activity import (
    get_user_activity_log, get_recent_logins,
    get_security_events, get_activity_summary
)
from .services_status import (
    get_user_status, set_status_message, clear_status_message,
    get_online_users, get_online_count, is_user_online
)


class TwoFactorAuthViewSet(viewsets.ViewSet):
    """
    ViewSet for Two-Factor Authentication
    
    Endpoints:
    - POST /api/users/2fa/enable/ - Enable 2FA
    - POST /api/users/2fa/verify/ - Verify and activate 2FA
    - POST /api/users/2fa/disable/ - Disable 2FA
    - GET /api/users/2fa/status/ - Get 2FA status
    - POST /api/users/2fa/regenerate-codes/ - Regenerate backup codes
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def enable(self, request):
        """Enable 2FA and get QR code"""
        try:
            secret_key, backup_codes, qr_code_url = enable_2fa(request.user)
            
            serializer = Enable2FAResponseSerializer(data={
                'secret_key': secret_key,
                'backup_codes': backup_codes,
                'qr_code_url': qr_code_url
            })
            serializer.is_valid(raise_exception=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """Verify 2FA code and activate"""
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success = verify_and_enable_2fa(
            request.user,
            serializer.validated_data['code']
        )
        
        if success:
            return Response({
                'message': '2FA enabled successfully',
                'enabled': True
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Invalid verification code',
                'enabled': False
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def disable(self, request):
        """Disable 2FA"""
        serializer = Disable2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify code before disabling
        if verify_2fa_code(request.user, serializer.validated_data['code']):
            disable_2fa(request.user)
            return Response({
                'message': '2FA disabled successfully',
                'enabled': False
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Invalid verification code'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get 2FA status"""
        enabled = is_2fa_enabled(request.user)
        return Response({
            'enabled': enabled
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='regenerate-codes')
    def regenerate_codes(self, request):
        """Regenerate backup codes"""
        backup_codes = regenerate_backup_codes(request.user)
        
        if backup_codes:
            return Response({
                'backup_codes': backup_codes,
                'message': 'Backup codes regenerated successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': '2FA not enabled'
            }, status=status.HTTP_400_BAD_REQUEST)


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
