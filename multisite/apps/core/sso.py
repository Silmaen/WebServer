"""Silent SSO for a site that is public first.

The intent: someone who already has an authentik session should arrive and simply
*be* logged in, with the console in place of the CV and no prompt of any kind.
Everyone else sees the guest site, with a discreet button in the header.

The obvious implementation -- redirect every anonymous visitor to authentik with
`prompt=none` -- is a trap on a site whose main job is to be publicly readable:

* it puts a redirect round-trip and a session cookie on every hit of the CV,
  including from crawlers, which is both slow and bad for indexing;
* and if the callback ever fails to mark the attempt, the homepage becomes a
  redirect loop. On a public page that is a visible outage, not a glitch.

So the attempt is made only for browsers that have signed in here before, marked by
a long-lived hint cookie set on login. A crawler never has one. A first-time visitor
is never redirected. The cost is that an SSO session in a brand-new browser is not
picked up until the user clicks the button once -- which is a fair trade for never
touching the anonymous path.
"""

import logging

from django.conf import settings
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from mozilla_django_oidc.views import OIDCAuthenticationRequestView

logger = logging.getLogger("apps")

# Set on login, read by the middleware. Not a security token: it only says "this
# browser has authenticated here at least once", so trying a silent check is worth a
# round-trip. Forging it costs an attacker a redirect and nothing else.
HINT_COOKIE = "sso_hint"
HINT_MAX_AGE = 60 * 60 * 24 * 365

# Marks "already tried in this session", which is what makes a loop impossible.
ATTEMPT_FLAG = "sso_silent_tried"

# Never attempted under these prefixes: the OIDC dance itself, the login and logout
# pages, the token endpoints the machines POST to, and static assets.
SKIP_PREFIXES = ("/oidc/", "/profile/", "/admin/", "/static/", "/media/", "/api/", "/markdownx/")


class SilentAuthRequestView(OIDCAuthenticationRequestView):
    """Start the OIDC dance with `prompt=none`: authenticate or fail, never ask.

    A subclass rather than `OIDC_AUTH_REQUEST_EXTRA_PARAMS`, because that setting
    would add `prompt=none` to *every* authentication request -- including the one
    behind the header button, which must be allowed to show authentik's login form.
    """

    def get_extra_params(self, request):
        params = super().get_extra_params(request)
        params["prompt"] = "none"
        return params


class SilentSSOMiddleware:
    """Try once, per session, to pick up an existing authentik session.

    Only for a browser carrying the hint cookie -- see the module docstring for why
    that condition is the whole design and not an optimisation.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _should_try(self, request):
        if not getattr(settings, "OIDC_ENABLED", False):
            return False
        if request.method != "GET":
            return False
        user = getattr(request, "user", None)
        if user is None or user.is_authenticated:
            return False
        if request.COOKIES.get(HINT_COOKIE) != "1":
            return False
        if request.session.get(ATTEMPT_FLAG):
            return False
        if any(request.path.startswith(p) for p in SKIP_PREFIXES):
            return False
        # An HTML page, not an asset fetch or an XHR: redirecting those breaks them
        # instead of logging anyone in.
        if "text/html" not in request.headers.get("Accept", ""):
            return False
        return not request.headers.get("HX-Request")

    def __call__(self, request):
        if self._should_try(request):
            # Written *before* the redirect, so even a callback that never comes back
            # cannot produce a second attempt. This is what keeps the homepage from
            # looping.
            request.session[ATTEMPT_FLAG] = True
            request.session.save()
            target = f"{reverse('oidc_silent')}?next={request.get_full_path()}"
            logger.debug("SSO silencieux tenté pour %s", request.path)
            return redirect(target)

        response = self.get_response(request)

        # Signing out has to also stop the silent attempt, or logout does not exist:
        # the Django session is cleared, the authentik one is not, and the next page
        # load logs the user straight back in. That is what happened -- an account
        # nobody could leave, on the monitoring page, with Django admin attached.
        #
        # Checked on the *request* path, so it covers the POST that performs the
        # logout, before any redirect.
        if self._is_logout(request):
            response.delete_cookie(HINT_COOKIE)
            return response

        # Set the hint on the way out rather than from a `user_logged_in` signal: a
        # signal has no response to attach a cookie to, and doing it here catches both
        # the local form and the OIDC callback with one rule.
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and request.COOKIES.get(HINT_COOKIE) != "1":
            remember_browser(response)
        return response

    @staticmethod
    def _is_logout(request):
        """Is this request the one that signs the user out?"""
        for name in ("logout", "oidc_logout"):
            try:
                if request.path == reverse(name):
                    return True
            except NoReverseMatch:
                continue
        return False


def remember_browser(response):
    """Mark this browser as one that has signed in, so the silent check is tried."""
    response.set_cookie(
        HINT_COOKIE, "1",
        max_age=HINT_MAX_AGE,
        secure=True,
        httponly=True,
        samesite="Lax",
    )
    return response


def oidc_logout_url(request):
    """Where to send the browser after clearing the Django session.

    RP-initiated logout, so signing out ends the **authentik** session too. Without
    it, logging out only drops the local session: the next click on "Sign in" is
    answered instantly from the still-valid SSO session, which makes logout look
    broken even once the hint cookie is gone.

    Falls back to the site root when no end-session endpoint is configured, which is
    what mozilla-django-oidc does on its own.
    """
    from urllib.parse import urlencode

    endpoint = getattr(settings, "OIDC_OP_LOGOUT_ENDPOINT", "")
    home = request.build_absolute_uri("/")
    if not endpoint:
        return home

    params = {"post_logout_redirect_uri": home}
    # authentik matches this against the provider's redirect URIs, so the id_token
    # hint is what lets it end the right session without asking anything.
    token = request.session.get("oidc_id_token")
    if token:
        params["id_token_hint"] = token
    separator = "&" if "?" in endpoint else "?"
    return f"{endpoint}{separator}{urlencode(params)}"
