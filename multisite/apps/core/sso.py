"""SSO silencieux pour un site d'abord public.

Une session authentik déjà ouverte doit connecter le visiteur sans rien demander,
mais rediriger *tout* anonyme vers authentik coûterait un aller-retour sur chaque
lecture du CV (crawlers compris) et pourrait boucler sur la page d'accueil. La
tentative est donc réservée aux navigateurs déjà venus, marqués par un cookie
indicateur : un crawler n'en a jamais, un premier visiteur n'est jamais redirigé.
"""

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from mozilla_django_oidc.views import OIDCAuthenticationRequestView

logger = logging.getLogger("apps")

# Posé à la connexion, lu par le middleware. Pas un jeton de sécurité : il dit
# seulement « ce navigateur s'est déjà authentifié ici », donc le forger ne coûte à
# un attaquant qu'une redirection.
HINT_COOKIE = "sso_hint"
HINT_MAX_AGE = 60 * 60 * 24 * 365

# Marque « déjà tenté dans cette session » : c'est ce qui rend une boucle impossible.
ATTEMPT_FLAG = "sso_silent_tried"

# Jamais tenté sous ces préfixes : la danse OIDC elle-même, les pages de connexion,
# les endpoints que les machines appellent, et les fichiers statiques.
SKIP_PREFIXES = ("/oidc/", "/profile/", "/admin/", "/static/", "/media/", "/api/", "/markdownx/")


class SilentAuthRequestView(OIDCAuthenticationRequestView):
    """Démarre la danse OIDC avec `prompt=none` : authentifier ou échouer, sans rien demander.

    Une sous-classe plutôt que `OIDC_AUTH_REQUEST_EXTRA_PARAMS`, qui ajouterait
    `prompt=none` à *toutes* les demandes — y compris celle du bouton de l'en-tête,
    qui doit pouvoir afficher le formulaire d'authentik.
    """

    def get_extra_params(self, request):
        """Ajoute `prompt=none` aux paramètres de la demande d'autorisation."""
        params = super().get_extra_params(request)
        params["prompt"] = "none"
        return params


class SilentSSOMiddleware:
    """Tente une fois par session de récupérer une session authentik existante.

    Uniquement pour un navigateur porteur du cookie indicateur — voir la docstring
    du module.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _should_try(self, request):
        """Cette requête vaut-elle une tentative silencieuse ?"""
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
        # Une page HTML, pas un asset ni un XHR : les rediriger les casse au lieu de
        # connecter qui que ce soit.
        if "text/html" not in request.headers.get("Accept", ""):
            return False
        return not request.headers.get("HX-Request")

    def __call__(self, request):
        if self._should_try(request):
            # Écrit *avant* la redirection : un callback qui ne revient jamais ne peut
            # donc pas produire une seconde tentative, ce qui évite la boucle.
            request.session[ATTEMPT_FLAG] = True
            request.session.save()
            target = f"{reverse('oidc_silent')}?next={request.get_full_path()}"
            logger.debug("SSO silencieux tenté pour %s", request.path)
            return redirect(target)

        response = self.get_response(request)

        # Sans ceci la déconnexion n'existe pas : la session Django est vidée, celle
        # d'authentik non, et la page suivante reconnecte aussitôt. Testé sur le
        # chemin de la *requête*, pour couvrir le POST qui déconnecte.
        if self._is_logout(request):
            response.delete_cookie(HINT_COOKIE)
            return response

        # Posé à la sortie plutôt que depuis un signal `user_logged_in` : un signal n'a
        # pas de réponse où accrocher un cookie, et une seule règle couvre ici le
        # formulaire local comme le callback OIDC.
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and request.COOKIES.get(HINT_COOKIE) != "1":
            remember_browser(response)
        return response

    @staticmethod
    def _is_logout(request):
        """Cette requête est-elle celle qui déconnecte l'utilisateur ?"""
        for name in ("logout", "oidc_logout"):
            try:
                if request.path == reverse(name):
                    return True
            except NoReverseMatch:
                continue
        return False


def remember_browser(response):
    """Marque ce navigateur comme déjà authentifié, pour tenter le SSO silencieux."""
    response.set_cookie(
        HINT_COOKIE, "1",
        max_age=HINT_MAX_AGE,
        secure=True,
        httponly=True,
        samesite="Lax",
    )
    return response


def oidc_logout_url(request):
    """Où envoyer le navigateur après avoir vidé la session Django.

    Déconnexion initiée par le RP, pour que se déconnecter termine aussi la session
    **authentik** : sinon le prochain « Se connecter » est servi instantanément par
    la session SSO encore ouverte. Repli sur la racine du site sans endpoint
    configuré.
    """
    endpoint = getattr(settings, "OIDC_OP_LOGOUT_ENDPOINT", "")
    home = request.build_absolute_uri("/")
    if not endpoint:
        return home

    params = {"post_logout_redirect_uri": home}
    # authentik s'en sert pour terminer la bonne session sans rien demander.
    token = request.session.get("oidc_id_token")
    if token:
        params["id_token_hint"] = token
    separator = "&" if "?" in endpoint else "?"
    return f"{endpoint}{separator}{urlencode(params)}"
