"""Métadonnées de page, navigation et filtrage des articles par niveau."""
import math

from django.shortcuts import get_object_or_404
from django.urls import reverse

from common.user_utils import (
    ADMINISTRATEUR, AUTORISE, AVANCE, ENREGISTRE, get_user_level,
)

from .models import Article, ProjetCategorie

articles_per_page = 10

ExternPages = []

page_info = {
    "accueil": {
        "Title": "Bienvenue",
    },
    "a_propos": {
        "Title": "À propos",
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
    "monitoring": {
        "Title": "Monitoring",
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

monitoring_subpages = [
    {"name": "Machines", "url": "monitoring", "icon": "mdi-server-network"},
    {"name": "Services", "url": "monitoring_services", "icon": "mdi-web"},
]

# Sous-navigation de la console. Déclarée ici avec le reste de la navigation, pour
# n'avoir qu'un seul endroit qui décrit les menus du site.
fleet_subpages = [
    {"name": "Machines", "url": "fleet:index", "icon": "mdi-server"},
    {"name": "Stacks", "url": "fleet:stacks", "icon": "mdi-layers-triple"},
]

admin_subpages = [
    {"name": "Utilisateurs", "url": "admin_users", "icon": "mdi-account-group"},
    {"name": "Projets", "url": "admin_projets", "icon": "mdi-pickaxe"},
    {"name": "Bricolages", "url": "admin_bricolages", "icon": "mdi-hammer-wrench"},
    {"name": "Services", "url": "admin_services", "icon": "mdi-monitor-dashboard"},
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
        "name": "À propos",
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
        "name": "Monitoring",
        "url": "monitoring",
        "icon": "mdi-monitor-dashboard",
        "group": "right",
        "Active": True,
        "MinLevel": ADMINISTRATEUR,
    },
    # La console, déclarée ici plutôt qu'écrite en dur dans le gabarit : c'est ce qui
    # la fait apparaître dans la navigation, filtrée par niveau comme le reste.
    {
        "name": "Flotte",
        "url": "fleet:index",
        "icon": "mdi-server",
        "group": "right",
        "Active": True,
        "MinLevel": AUTORISE,
    },
    {
        "name": "Appareils",
        "url": "devices:list",
        "icon": "mdi-lan",
        "group": "right",
        "Active": True,
        "MinLevel": AUTORISE,
    },
    {
        "name": "Réseaux",
        "url": "network:list",
        "icon": "mdi-sitemap",
        "group": "right",
        "Active": True,
        "MinLevel": ADMINISTRATEUR,
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
    Articles d'une catégorie, filtrés selon les privilèges de l'utilisateur.
     :param user : L'utilisateur courant.
     :param category : L'identifiant de la catégorie.
     :return : Le queryset filtré.
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
    Une page de news, et la liste des numéros de page.
     :param user : L'utilisateur courant.
     :param page : Le numéro de page demandé.
     :return : Tuple (articles de la page, liste des numéros de page).
    """
    articles = get_articles(user, 1)
    total = articles.count()
    nb_page = max(1, math.ceil(total / articles_per_page))
    pages = list(range(1, nb_page + 1))
    return articles[(page - 1) * articles_per_page: page * articles_per_page], pages


def get_article(user, article_id):
    """
    Un article, ou None si l'utilisateur n'a pas le droit de le voir.
     :param user : L'utilisateur courant.
     :param article_id : L'identifiant de l'article.
     :return : L'article, ou None.
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
    """Les pages externes que l'utilisateur a le droit de voir."""
    return _filter_pages(ExternPages, get_user_level(user))


def get_int_pages(user):
    """Les pages internes que l'utilisateur a le droit de voir."""
    return _filter_pages(internal_pages, get_user_level(user))


def get_page_data(user, page_name):
    """
    Le contexte de base d'une page : titre, repère de navigation, sous-pages.

    Les données de navigation elles-mêmes viennent du context processor
    `www.context_processors.navigation`.
     :param user : L'utilisateur courant.
     :param page_name : La clé de la page dans `page_info`.
     :return : Le dict de contexte, vide si la page est inconnue.
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
    elif page_name == "monitoring":
        data["subpages"] = monitoring_subpages
    elif page_name == "administration":
        data["subpages"] = admin_subpages
    return data
