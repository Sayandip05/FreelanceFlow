from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission that allows only object owners or admin users.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return hasattr(obj, 'user') and obj.user == request.user


class BaseRolePermission(permissions.BasePermission):
    """
    Base class for role-based permissions.
    """
    required_role = None
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and
            request.user.role == self.required_role
        )


class IsClient(BaseRolePermission):
    """
    Permission that allows only clients.
    """
    required_role = "CLIENT"


class IsFreelancer(BaseRolePermission):
    """
    Permission that allows only freelancers.
    """
    required_role = "FREELANCER"


class IsOwner(permissions.BasePermission):
    """
    Permission that allows only the object owner.
    Assumes the object has a 'user' attribute.
    """
    
    def has_object_permission(self, request, view, obj):
        return hasattr(obj, 'user') and obj.user == request.user
