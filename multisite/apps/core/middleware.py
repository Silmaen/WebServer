"""Custom middleware for access control."""

from django.shortcuts import render


class InactiveUserMiddleware:
    """Redirect authenticated users without authorized group to the forbidden page.

    OIDC users not in 'viewers' or 'admins' groups (and not superuser)
    see a 403 page with a logout button.
    """

    ALLOWED_PATHS = ("/accounts/logout/", "/accounts/login/", "/admin/", "/oidc/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user is not None
            and user.is_authenticated
            and not user.is_superuser
            and not user.is_staff
            and not any(request.path.startswith(p) for p in self.ALLOWED_PATHS)
            and not user.groups.filter(name__in=["viewers", "admins"]).exists()
        ):
            return render(request, "core/forbidden.html", status=403)
        return self.get_response(request)
