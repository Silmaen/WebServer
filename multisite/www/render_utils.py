"""
gathering functions to render pages
"""
import math

from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import Article, ProjetCategorie
from common.user_utils import (
    get_user_level, user_is_autorise, user_is_avance, user_is_administrateur,
    ENREGISTRE, AUTORISE, AVANCE, ADMINISTRATEUR,
)

articles_per_page = 10

ExternPages = []

page_info = {
    "accueil": {
        "Title": "Bienvenue",
    },
    "a_propos": {
        "Title": "\u00c0 propos",
    },
    "mes_projets": {
        "Title": "Mes projets",
    },
    "archives": {
        "Title": "Archives",
    },
    "bricolage": {
        "Title": "Bricolage",
    },
    "administration": {
        "Title": "Administration",
    },
}

archives_subpages = [
    {"name": "News", "url": "archives_news", "icon": "mdi-newspaper"},
    {"name": "Recherche", "url": "archives_research", "icon": "mdi-electron-framework"},
]

a_propos_subpages = [
    {"name": "CV", "url": "a_propos_cv", "icon": "mdi-file-account"},
    {"name": "Publications", "url": "a_propos_publications", "icon": "mdi-book-open-variant"},
]

admin_subpages = [
    {"name": "Utilisateurs", "url": "admin_users", "icon": "mdi-account-group"},
    {"name": "Projets", "url": "admin_projets", "icon": "mdi-pickaxe"},
    {"name": "Bricolages", "url": "admin_bricolages", "icon": "mdi-hammer-wrench"},
]


internal_pages = [
    {
        "name": "Accueil",
        "url": "accueil",
        "icon": "mdi-home",
        "group": "left",
        "Active": True,
        "MinLevel": -1,
    },
    {
        "name": "\u00c0 propos",
        "url": "a_propos",
        "icon": "mdi-account",
        "group": "left",
        "Active": True,
        "MinLevel": -1,
    },
    {
        "name": "Mes projets",
        "url": "mes_projets",
        "icon": "mdi-pickaxe",
        "group": "left",
        "Active": True,
        "MinLevel": -1,
    },
    {
        "name": "Archives",
        "url": "archives",
        "icon": "mdi-archive",
        "group": "right",
        "Active": True,
        "MinLevel": AVANCE,
    },
    {
        "name": "Bricolage",
        "url": "bricolage",
        "icon": "mdi-hammer-wrench",
        "group": "left",
        "Active": True,
        "MinLevel": AVANCE,
    },
    {
        "name": "Administration",
        "url": "administration",
        "icon": "mdi-cog",
        "group": "right",
        "Active": True,
        "MinLevel": ADMINISTRATEUR,
    },
]


def _filter_pages(pages, user_level):
    """Filtre une liste de pages selon le niveau utilisateur."""
    return [p for p in pages if p["Active"] and p["MinLevel"] <= user_level]


def _get_projet_subpages():
    """Retourne les sous-pages dynamiques des catégories de projets."""
    categories = ProjetCategorie.objects.all()
    return [
        {
            "name": cat.nom,
            "href": reverse("mes_projets_categorie", args=[cat.slug]),
            "icon": f"mdi-{cat.mdi_icon_name}" if cat.mdi_icon_name else "",
        }
        for cat in categories
    ]


def get_articles(user, category):
    """
    Permet de r\u00e9cup\u00e9rer les articles de la cat\u00e9gorie en fonction des privil\u00e8ges de l'utilisateur.
    """
    level = get_user_level(user)
    qs = Article.objects.filter(categorie=category)
    if level >= ADMINISTRATEUR:
        return qs
    if level < AVANCE:
        qs = qs.filter(developper=False)
    if level < AUTORISE:
        qs = qs.filter(superprivate=False)
    if level < ENREGISTRE:
        qs = qs.filter(private=False)
    return qs


def get_news_articles(user, page):
    """
    Permet de r\u00e9cup\u00e9rer les articles de la cat\u00e9gorie en fonction des privil\u00e8ges de l'utilisateur.
    """
    articles = get_articles(user, 1)
    total = articles.count()
    nb_page = max(1, math.ceil(total / articles_per_page))
    pages = list(range(1, nb_page + 1))
    return articles[(page - 1) * articles_per_page: page * articles_per_page], pages


def get_article(user, article_id):
    """
    Permet de r\u00e9cup\u00e9rer un article en fonction des privil\u00e8ges de l'utilisateur.
    """
    article = get_object_or_404(Article, pk=article_id)
    level = get_user_level(user)
    if article.staff and level < ADMINISTRATEUR:
        return None
    if article.developper and level < AVANCE:
        return None
    if article.superprivate and level < AUTORISE:
        return None
    if article.private and level < ENREGISTRE:
        return None
    return article


def get_ext_pages(user):
    """
    Renvoie la liste de pages externe que l'user a le droit de voir.
    """
    return _filter_pages(ExternPages, get_user_level(user))


def get_int_pages(user):
    """
    Renvoie la liste de pages interne que l'user a le droit de voir.
    """
    return _filter_pages(internal_pages, get_user_level(user))


def get_page_data(user, page_name):
    """
    Permet de r\u00e9cup\u00e9rer les infos li\u00e9es \u00e0 la page courante pour l'user.
    Les donn\u00e9es de navigation (pages_left, pages_right, extpages) sont
    fournies par le context processor www.context_processors.navigation.
    """
    if page_name not in page_info:
        return {}
    data = {
            "page_subtitle": page_info[page_name]["Title"],
            "page": page_name,
            "subpage": ""}
    if page_name == "a_propos":
        data["subpages"] = a_propos_subpages
    elif page_name == "mes_projets":
        data["subpages"] = _get_projet_subpages()
    elif page_name == "archives":
        data["subpages"] = archives_subpages
    elif page_name == "administration":
        data["subpages"] = admin_subpages
    return data
