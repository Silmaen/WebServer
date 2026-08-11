"""Ce que la racine du site affiche, et à qui.

`argawaen.net` est deux choses à la même adresse : un CV et des projets publics pour
tout le monde, la supervision du homelab pour qui a le droit de la voir. La racine
répartit donc, en deux niveaux, car le site en avait déjà deux : un administrateur
voit le monitoring de `www` (réservé à ce niveau), un simple autorisé la page de la
flotte, faite pour la lecture seule. La page admin est *appelée* et non redirigée,
pour que l'adresse reste `/`.
"""

from django.shortcuts import redirect

from .views import a_propos, monitoring, user_is_administrateur

# Les groupes Django sur lesquels le backend OIDC projette ceux d'authentik. Vérifiés
# ici plutôt qu'en dur, pour qu'un renommage côté authentik reste une variable
# d'environnement.
VIEWER_GROUPS = ("viewers", "admins")


def is_admin(user):
    """Cet utilisateur peut-il voir le monitoring de `www`, réservé aux administrateurs ?"""
    return user.is_authenticated and (user.is_superuser or user_is_administrateur(user))


def is_viewer(user):
    """Cet utilisateur peut-il voir le lab, ne serait-ce qu'en lecture ?"""
    if not user.is_authenticated:
        return False
    return user.is_staff or user.groups.filter(name__in=VIEWER_GROUPS).exists()


def home(request):
    """
    Les infos personnelles pour un invité, le monitoring pour une session autorisée.

    `a_propos` et non `accueil` : la page d'accueil générique n'apprend rien à un
    visiteur venu voir qui on est ; les infos personnelles, si.
     :param request : La requête du client.
     :return : La page rendue ou une redirection vers la console.
    """
    if is_admin(request.user):
        return monitoring(request)
    if is_viewer(request.user):
        # Lecture seule : la console plutôt que le monitoring de www, réservé aux admins.
        return redirect("fleet:index")
    return a_propos(request)
