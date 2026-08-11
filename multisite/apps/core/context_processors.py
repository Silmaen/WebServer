"""Contexte de gabarit partagé par le site public et la console."""

from django.conf import settings


def sso(request):
    """Indique si le SSO est configuré, pour que l'en-tête le propose en premier.

    Lu depuis les réglages plutôt que testé dans chaque gabarit : `OIDC_ENABLED` vaut
    déjà « OIDC_RP_CLIENT_ID est renseigné », et sans lui seul le formulaire local a
    un sens.
    """
    return {
        "oidc_enabled": getattr(settings, "OIDC_ENABLED", False),
        # Noms des groupes authentik, pour que la page 403 dise lequel demander.
        "oidc_admin_group": getattr(settings, "OIDC_ADMIN_GROUP", ""),
        "oidc_viewer_group": getattr(settings, "OIDC_VIEWER_GROUP", ""),
    }
