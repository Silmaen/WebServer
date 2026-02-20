"""Quelques fonctions utiles pour la gestion des utilisateurs"""

# Niveaux utilisateur
ENREGISTRE = 0
AUTORISE = 1
AVANCE = 2
ADMINISTRATEUR = 3

USER_LEVEL_CHOICES = [
    (ENREGISTRE, "Enregistr\u00e9"),
    (AUTORISE, "Autoris\u00e9"),
    (AVANCE, "Avanc\u00e9"),
    (ADMINISTRATEUR, "Administrateur"),
]


def get_user_level(user):
    """
    Retourne le niveau de l'utilisateur.
    -1 si non authentifi\u00e9, sinon la valeur de user_level sur le profil.
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
    """Teste si l'utilisateur est au moins autoris\u00e9 (niveau >= 1)."""
    return get_user_level(user) >= AUTORISE


def user_is_avance(user):
    """Teste si l'utilisateur est au moins avanc\u00e9 (niveau >= 2)."""
    return get_user_level(user) >= AVANCE


def user_is_administrateur(user):
    """Teste si l'utilisateur est administrateur (niveau >= 3)."""
    return get_user_level(user) >= ADMINISTRATEUR


# Alias de compatibilit\u00e9
def user_is_validated(user):
    """Alias pour user_is_autorise."""
    return user_is_autorise(user)


def user_is_developper(user):
    """Alias pour user_is_avance."""
    return user_is_avance(user)


def user_is_moderator(user):
    """Alias pour user_is_avance."""
    return user_is_avance(user)
