"""Context processor fournissant les données de navigation à tous les templates."""
from .render_utils import get_ext_pages, get_int_pages


def navigation(request):
    """Ajoute les pages de navigation (gauche/droite + externes) au contexte."""
    user = request.user
    int_pages = get_int_pages(user)
    return {
        'pages_left': [p for p in int_pages if p.get("group") == "left"],
        'pages_right': [p for p in int_pages if p.get("group") == "right"],
        'extpages': get_ext_pages(user),
    }
