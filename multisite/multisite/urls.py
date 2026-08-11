"""Configuration des URL du projet multisite."""
from django.contrib import admin
from django.urls import include, path

from apps.core.sso import SilentAuthRequestView
from www.urls import urlpatterns as www_patterns
from www.views_home import home

# La console vit sous /console/, pour que le site public garde toutes ses URL.
console_patterns = [
    path("", include("apps.dashboard.urls")),
    path("fleet/", include("apps.fleet.urls")),
    path("devices/", include("apps.devices.urls")),
    path("networks/", include("apps.network.urls")),
    path("monitoring/", include("apps.monitoring.urls")),
    path("", include("apps.core.urls")),
]

urlpatterns = [
    # Avant www_patterns pour gagner sur '' : la racine montre le CV à un invité et le
    # monitoring à une session autorisée. Voir www/views_home.py.
    path("", home),
] + www_patterns + [
    # prompt=none, pour le middleware qui récupère une session authentik existante sans
    # jamais afficher de formulaire. Sa propre route, car le bouton de l'en-tête doit
    # pouvoir afficher la page de connexion d'authentik.
    path("oidc/silent/", SilentAuthRequestView.as_view(), name='oidc_silent'),
    path("profile/", include("connector.urls")),
    path("console/", include(console_patterns)),
    # Endpoints à jeton porteur auxquels les machines postent, délibérément hors des
    # défauts DRF, qui exigent un utilisateur connecté.
    path("api/fleet/", include("apps.fleet.api_urls")),
    path("api/", include("apps.api.urls")),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("admin/", admin.site.urls),
    path("markdownx/", include("markdownx.urls")),
]
