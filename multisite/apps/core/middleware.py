"""Middleware de contrôle d'accès à la console."""

from django.shortcuts import render


class InactiveUserMiddleware:
    """Affiche un 403 propre à un connecté qui n'a pas le droit de voir la console.

    Volontairement limité aux préfixes de la console : une version non restreinte
    interdisait aux membres ordinaires l'accueil, les articles et leur propre profil,
    alors que les anonymes passaient. Les vues de la console vérifient déjà
    l'appartenance ; ce middleware n'ajoute que la page 403 honnête, au lieu d'une
    redirection vers une connexion déjà faite.
    """

    GUARDED_PREFIXES = ("/console/",)

    # Joignables même bloqué, pour pouvoir sortir de la page 403.
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
            return render(request, "core/forbidden.html", {
                "page_subtitle": "Accès refusé",
            }, status=403)
        return self.get_response(request)
