"""
Serializers for Extended User Features
"""
from rest_framework import serializers
from apps.users.models.models_extended import ActivityLog, UserOnlineStatus


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
