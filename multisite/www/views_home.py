"""What the root of the site shows, and to whom.

`argawaen.net` is two things at one address: a CV and some public projects for
anyone, and the homelab's monitoring for whoever is allowed to see it. So `/`
dispatches instead of being a single page — a guest gets the CV, an authorised
session gets the monitoring, and neither has to know the other exists.

Two tiers, because the site already had two. authentik's `admin domain` maps to the
Django group `admins` and `user home` to `viewers`, and `www`'s own monitoring page
is decorated `@admin_required` — so a viewer cannot be sent there, it would answer
403. A viewer gets the console's fleet page instead, which is built for read-only
access. Both land on "the monitoring"; each on the one they may see.

The admin page is *called*, not redirected to, so the address stays `/` — which is
the point of "the main page becomes the monitoring".
"""

from django.shortcuts import redirect

from .views import accueil, monitoring, user_is_administrateur

# The Django groups the OIDC backend maps authentik's groups onto. Checked here
# rather than hardcoding authentik's names, so renaming a group there stays one env
# var and no code change.
VIEWER_GROUPS = ("viewers", "admins")


def is_admin(user):
    """May this user see `www`'s monitoring, which is admin-only?"""
    return user.is_authenticated and (user.is_superuser or user_is_administrateur(user))


def is_viewer(user):
    """May this user see the lab at all, read-only included?"""
    if not user.is_authenticated:
        return False
    return user.is_staff or user.groups.filter(name__in=VIEWER_GROUPS).exists()


def home(request):
    """The CV for a guest, the monitoring for an authorised session."""
    if is_admin(request.user):
        return monitoring(request)
    if is_viewer(request.user):
        # Read-only: the console's fleet page rather than www's admin monitoring.
        return redirect("fleet:index")
    return accueil(request)
