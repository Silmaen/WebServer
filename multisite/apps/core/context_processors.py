"""Template context shared by the public site and the console."""

from django.conf import settings


def sso(request):
    """Whether SSO is configured, so the header can offer it as the primary button.

    Read from settings rather than tested per template: `OIDC_ENABLED` is already
    "OIDC_RP_CLIENT_ID is set", and with it empty the whole flow is off and only the
    local form makes sense.
    """
    return {"oidc_enabled": getattr(settings, "OIDC_ENABLED", False)}
