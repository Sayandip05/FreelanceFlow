"""
Serializers for Extended User Features
"""
from rest_framework import serializers
from .models_extended import TwoFactorAuth, ActivityLog, UserOnlineStatus


# ============= 2FA Serializers =============

class Enable2FASerializer(serializers.Serializer):
    """Serializer for enabling 2FA (no input needed)"""
    pass


class Verify2FASerializer(serializers.Serializer):
    """Serializer for verifying 2FA code"""
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text="6-digit TOTP code from authenticator app"
    )


class Disable2FASerializer(serializers.Serializer):
    """Serializer for disabling 2FA"""
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text="6-digit TOTP code to confirm disable"
    )


class TwoFactorAuthStatusSerializer(serializers.ModelSerializer):
    """Serializer for 2FA status"""
    class Meta:
        model = TwoFactorAuth
        fields = ['is_enabled', 'last_used_at']
        read_only_fields = ['is_enabled', 'last_used_at']


class Enable2FAResponseSerializer(serializers.Serializer):
    """Response after enabling 2FA"""
    secret_key = serializers.CharField()
    backup_codes = serializers.ListField(child=serializers.CharField())
    qr_code_url = serializers.CharField()
    message = serializers.CharField(default="Scan QR code with authenticator app and verify")


# ============= Activity Log Serializers =============

class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for activity logs"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user_email', 'action', 'resource_type', 
            'resource_id', 'ip_address', 'user_agent', 
            'metadata', 'created_at'
        ]
        read_only_fields = fields


class ActivitySummarySerializer(serializers.Serializer):
    """Serializer for activity summary"""
    action = serializers.CharField()
    count = serializers.IntegerField()


# ============= Online Status Serializers =============

class UserOnlineStatusSerializer(serializers.ModelSerializer):
    """Serializer for user online status"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserOnlineStatus
        fields = ['user_email', 'user_name', 'is_online', 'last_seen', 'status_message']
        read_only_fields = ['user_email', 'user_name', 'is_online', 'last_seen']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class UpdateStatusMessageSerializer(serializers.Serializer):
    """Serializer for updating status message"""
    status_message = serializers.CharField(
        max_length=200,
        allow_blank=True,
        required=False,
        help_text="Custom status message"
    )


class OnlineUsersSerializer(serializers.Serializer):
    """Serializer for online users list"""
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()
    is_online = serializers.BooleanField()
    last_seen = serializers.DateTimeField()
