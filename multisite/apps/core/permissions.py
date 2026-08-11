"""Permissions DRF, alignées sur les mixins de vues."""

from rest_framework.permissions import BasePermission


class IsViewer(BasePermission):
    """Utilisateur connecté du groupe "viewers" ou "admins" (ou superuser/staff)."""

    def has_permission(self, request, view):
        """Autorise la lecture aux membres des groupes de la console."""
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return user.groups.filter(name__in=["viewers", "admins"]).exists()


class IsAdmin(BasePermission):
    """Utilisateur staff : groupe "admins" ou superuser."""

    def has_permission(self, request, view):
        """Autorise l'écriture au staff uniquement."""
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or user.is_staff
