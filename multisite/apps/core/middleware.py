"""Custom middleware for access control."""

from django.shortcuts import render


class InactiveUserMiddleware:
    """Show a clean 403 to a logged-in user who may not see the console.

    **Scoped to the console on purpose.** This came from network_monitor, where the
    whole application *was* the console, so guarding every path was right. Here it is
    not: argawaen.net is a public site with its own registration, and an unscoped
    version locked every ordinary logged-in member out of the homepage, the articles
    and even their own profile — anonymous visitors got 200, members got 403. Which is
    the worst shape a bug can take, because you only see it once you log in.

    The console views already enforce membership themselves through
    `ViewerRequiredMixin`; what this adds is the honest 403 page instead of a redirect
    back to a login the user has already passed.
    """

    # Only these prefixes are guarded. Everything else -- the whole public site -- is
    # none of this middleware's business.
    GUARDED_PREFIXES = ("/console/",)

    # Reachable even while blocked, so a user who lands on the 403 can get out of it.
    # `/profile/` is this site's own login and logout, not the /accounts/ paths
    # network_monitor used.
    ALLOWED_PATHS = ("/profile/login/", "/profile/logout/", "/admin/", "/oidc/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user is not None
            and user.is_authenticated
            and not user.is_superuser
            and not user.is_staff
            and any(request.path.startswith(p) for p in self.GUARDED_PREFIXES)
            and not any(request.path.startswith(p) for p in self.ALLOWED_PATHS)
            and not user.groups.filter(name__in=["viewers", "admins"]).exists()
        ):
            return render(request, "core/forbidden.html", status=403)
        return self.get_response(request)
