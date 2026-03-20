from rest_framework.permissions import BasePermission, SAFE_METHODS


class StaffWriteOtherwiseReadOnly(BasePermission):
    """Allow any authenticated user to read; only staff/superusers may write."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))
