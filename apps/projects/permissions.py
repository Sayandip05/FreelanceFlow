from rest_framework import permissions

from .models import Project


class IsProjectOwner(permissions.BasePermission):
    """
    Permission that allows only the project owner (client).
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.client == request.user


class IsProjectClient(permissions.BasePermission):
    """
    Permission that checks if user is the client who posted the project.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.client == request.user


class IsOpenProject(permissions.BasePermission):
    """
    Permission that checks if project is open for bidding.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.status == Project.Status.OPEN
