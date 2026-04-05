from rest_framework import permissions

class IsAdminRoleOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    All users (even unauthenticated) can view (GET, HEAD, OPTIONS).
    """

    def has_permission(self, request, view):
        # Allow read-only methods for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to authenticated admin users
        return (
            request.user and 
            request.user.is_authenticated and 
            (getattr(request.user, 'role', '') == 'admin' or request.user.is_staff)
        )
