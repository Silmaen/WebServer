"""Permission mixins for view access control.

Two levels:
- ViewerRequiredMixin: authenticated + in group "viewers" or "admins" (or superuser)
- StaffRequiredMixin: authenticated + is_staff (admins only)
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class ViewerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict access to authorized users (viewers or admins)."""

    def test_func(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return True
        return user.groups.filter(name__in=["viewers", "admins"]).exists()


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict access to staff users (admins)."""

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.is_staff
