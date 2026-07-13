from rest_framework import permissions
class CanSearch(permissions.BasePermission):
    """
    Permission that allows authenticated users to perform search.
    Public search (AllowAny) is kept as default in views.
    This permission is for restricted search endpoints.
    """
    
    def has_permission(self, request, view):
        # Read-only search is allowed for anyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write operations (reindex etc.) require staff
        return request.user and request.user.is_staff
