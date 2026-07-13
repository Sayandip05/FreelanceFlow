from rest_framework import permissions
class IsNotificationOwner(permissions.BasePermission):
    """
    Permission that allows only the recipient of a notification.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.recipient == request.user


class CanManageNotifications(permissions.BasePermission):
    """
    Permission that restricts notification management to authenticated users.
    Users can only access their own notifications.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
