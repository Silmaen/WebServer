"""Quelques fonctions utiles pour la gestion des utilisateurs"""

# Niveaux utilisateur
ENREGISTRE = 0
AUTORISE = 1
AVANCE = 2
ADMINISTRATEUR = 3

USER_LEVEL_CHOICES = [
    (ENREGISTRE, "Enregistré"),
    (AUTORISE, "Autorisé"),
    (AVANCE, "Avancé"),
    (ADMINISTRATEUR, "Administrateur"),
]


def get_user_level(user):
    """
    Le niveau de l'utilisateur : -1 s'il n'est pas authentifié.
     :param user : L'utilisateur à tester.
     :return : Le niveau, entre -1 et ADMINISTRATEUR.
    """
    if not user.is_authenticated:
        return -1
    if user.is_superuser:
        return ADMINISTRATEUR
    try:
        return user.userprofile.user_level
    except Exception:
        return ENREGISTRE


def user_is_autorise(user):
    """Teste si l'utilisateur est au moins autorisé (niveau >= 1)."""
    return get_user_level(user) >= AUTORISE


def user_is_avance(user):
    """Teste si l'utilisateur est au moins avancé (niveau >= 2)."""
    return get_user_level(user) >= AVANCE


def user_is_administrateur(user):
    """Teste si l'utilisateur est administrateur (niveau >= 3)."""
    return get_user_level(user) >= ADMINISTRATEUR


# Alias de compatibilité
def user_is_validated(user):
    """Alias pour user_is_autorise."""
    return user_is_autorise(user)


def user_is_developper(user):
    """Alias pour user_is_avance."""
    return user_is_avance(user)


def user_is_moderator(user):
    """Alias pour user_is_avance."""
    return user_is_avance(user)
