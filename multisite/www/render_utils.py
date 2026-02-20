"""
gathering functions to render pages
"""
import math

from django.shortcuts import get_object_or_404

from .models import Article
from common.user_utils import user_is_developper, user_is_validated

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
    "administration": {
        "Title": "Administration",
    },
}

archives_subpages = [
    {"name": "News", "url": "archives_news", "icon": "mdi-newspaper"},
    {"name": "Recherche", "url": "archives_research", "icon": "mdi-electron-framework"},
]


internal_pages = [
    {
        "name": "Accueil",
        "url": "accueil",
        "icon": "mdi-home",
        "group": "left",
        "Active": True,
        "NeedUser": False,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": False,
    },
    {
        "name": "À propos",
        "url": "a_propos",
        "icon": "mdi-account",
        "group": "left",
        "Active": True,
        "NeedUser": False,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": False,
    },
    {
        "name": "Mes projets",
        "url": "mes_projets",
        "icon": "mdi-pickaxe",
        "group": "left",
        "Active": True,
        "NeedUser": False,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": False,
    },
    {
        "name": "Archives",
        "url": "archives",
        "icon": "mdi-archive",
        "group": "right",
        "Active": True,
        "NeedUser": True,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": False,
    },
    {
        "name": "Bricolage",
        "url": "bricolage",
        "icon": "mdi-hammer-wrench",
        "group": "left",
        "Active": True,
        "NeedUser": True,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": False,
    },
    {
        "name": "Administration",
        "url": "administration",
        "icon": "mdi-cog",
        "group": "right",
        "Active": True,
        "NeedUser": True,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": False,
    },
]


def get_articles(user, category):
    """
    Permet de récupérer les articles de la catégorie en fonction des privilèges de l'utilisateur.
    :param user:
    :param category:
    :return:
    """
    if not user.is_authenticated:
        return Article.objects.filter(categorie=category, private=False)
    elif not user.is_staff:
        return Article.objects.filter(categorie=category, staff=False)
    else:
        return Article.objects.filter(categorie=category)


def get_news_articles(user, page):
    """
    Permet de récupérer les articles de la catégorie en fonction des privilèges de l'utilisateur.
    :param user:
    :param page:
    :return:
    """
    articles = get_articles(user, 1)
    total = articles.count()
    nb_page = max(1, math.ceil(total / articles_per_page))
    pages = list(range(1, nb_page + 1))
    return articles[(page - 1) * articles_per_page: page * articles_per_page], pages


def get_article(user, article_id):
    """
    Permet de récupérer les articles de la catégorie en fonction des privilèges de l'utilisateur.
    :param user:
    :param article_id:
    :return:
    """
    article = get_object_or_404(Article, pk=article_id)
    if not user.is_authenticated and article.private:
        return None
    elif not user.is_staff and article.staff:
        return None
    return article


def get_ext_pages(user):
    """
    Renvoie la liste de pages externe que l'user a le droit de voir.
    :param user:
    :return:
    """
    ext_pages = []
    if user.is_staff:
        for e in ExternPages:
            if not e["Active"]:
                continue
            ext_pages.append(e)
        return ext_pages

    for e in ExternPages:
        if e["NeedStaff"] or not e["Active"]:
            continue
        if not user.is_authenticated and e["NeedUser"]:
            continue
        if not user_is_developper(user) and e["NeedDev"]:
            continue
        if not user_is_validated(user) and e["NeedValidatedUser"]:
            continue
        ext_pages.append(e)
    return ext_pages


def get_int_pages(user):
    """
    Renvoie la liste de pages externe que l'user a le droit de voir.
    :param user:
    :return:
    """
    int_pages = []
    if user.is_staff:
        for e in internal_pages:
            if not e["Active"]:
                continue
            int_pages.append(e)
        return int_pages

    for e in internal_pages:
        if e["NeedStaff"] or not e["Active"]:
            continue
        if not user.is_authenticated and e["NeedUser"]:
            continue
        if not user_is_developper(user) and e["NeedDev"]:
            continue
        if not user_is_validated(user) and e["NeedValidatedUser"]:
            continue
        int_pages.append(e)
    return int_pages


def get_page_data(user, page_name):
    """
    Permet de récupérer les infos liées à la page courante pour l'user.
    Les données de navigation (pages_left, pages_right, extpages) sont
    fournies par le context processor www.context_processors.navigation.
    :param user:
    :param page_name:
    :return:
    """
    if page_name not in page_info:
        return {}
    data = {
            "page_subtitle": page_info[page_name]["Title"],
            "page": page_name,
            "subpage": ""}
    if page_name == "archives":
        data["subpages"] = archives_subpages
    return data
