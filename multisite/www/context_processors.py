"""Context processor fournissant les données de navigation à tous les templates."""
from common.user_utils import get_user_level, user_is_administrateur, AVANCE
from .render_utils import get_ext_pages, get_int_pages


def navigation(request):
    """Ajoute les pages de navigation (gauche/droite + externes) au contexte."""
    user = request.user
    int_pages = get_int_pages(user)
    level = get_user_level(user)
    ctx = {
        'pages_left': [p for p in int_pages if p.get("group") == "left"],
        'pages_right': [p for p in int_pages if p.get("group") == "right"],
        'extpages': get_ext_pages(user),
        'is_admin': user_is_administrateur(user) if user.is_authenticated else False,
        'user_level': level,
    }
    if user.is_authenticated:
        ctx['user_level_display'] = user.userprofile.get_user_level_display()
        ctx['user_is_avance'] = level >= AVANCE
    return ctx
