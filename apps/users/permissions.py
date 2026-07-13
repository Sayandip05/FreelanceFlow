from rest_framework import permissions
from .models import User


class IsFreelancer(permissions.BasePermission):
    """
    Permission that allows only freelancers.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.Roles.FREELANCER
        )


class IsClient(permissions.BasePermission):
    """
    Permission that allows only clients.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.Roles.CLIENT
        )


class IsOwner(permissions.BasePermission):
    """
    Permission that allows only the object owner.
    Assumes the object has a 'user' attribute.
    """
    
    def has_object_permission(self, request, view, obj):
        return hasattr(obj, 'user') and obj.user == request.user


class IsSelf(permissions.BasePermission):
    """
    Permission that allows users to only access their own data.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj == request.user
