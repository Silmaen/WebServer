"""DRF permission classes matching the view mixins."""

from rest_framework.permissions import BasePermission


class IsViewer(BasePermission):
    """Authenticated user in 'viewers' or 'admins' group (or superuser/staff)."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return user.groups.filter(name__in=["viewers", "admins"]).exists()


class IsAdmin(BasePermission):
    """Staff user (admin group or superuser)."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or user.is_staff
