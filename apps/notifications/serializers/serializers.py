from rest_framework import serializers
from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "body",
            "type",
            "is_read",
            "created_at"
        ]
        read_only_fields = ["id", "created_at"]


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of notification IDs to mark as read. If empty, marks all as read."
    )
