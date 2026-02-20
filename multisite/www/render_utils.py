"""
gathering functions to render pages
"""
import math

from django.shortcuts import get_object_or_404

from .models import Article
from common.user_utils import user_is_developper, user_is_validated

articles_per_page = 10

ExternPages = [
    {
        "name": "Site Principal",
        "url": "https://www.argawaen.net",
        "icon": "",
        "Active": True,
        "NeedUser": False,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": False,
     },
    {
        "name": "Mantis",
        "url": "https://mantis.argawaen.net",
        "icon": "",
        "Active": True,
        "NeedUser": True,
        "NeedStaff": True,
        "NeedDev": True,
        "NeedValidatedUser": True,
     },
    {
        "name": "Builder",
        "url": "https://builder.argawaen.net",
        "icon": "",
        "Active": True,
        "NeedUser": True,
        "NeedStaff": True,
        "NeedDev": True,
        "NeedValidatedUser": True,
     }
]

page_info = {
    "news": {
        "Title": "La page des news",
    },
    "research": {
        "Title": "La page des recherches",
    },
    "projects": {
        "Title": "La page des projets",
    },
    "links": {
        "Title": "La page des liens",
    },
}


internal_pages = [
    {
        "name": "News",
        "url": "index",
        "icon": "mdi-home",
        "Active": True,
        "NeedUser": False,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": False,
    },
    {
        "name": "Recherche",
        "url": "research",
        "icon": "mdi-electron-framework",
        "Active": True,
        "NeedUser": False,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": False,
    },
    {
        "name": "Projets",
        "url": "projects",
        "icon": "mdi-pickaxe",
        "Active": True,
        "NeedUser": False,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": False,
    },
    {
        "name": "Liens",
        "url": "links",
        "icon": "mdi-link",
        "Active": True,
        "NeedUser": True,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": True,
    },
    {
        "name": "Server admin",
        "url": "admin:index",
        "icon": "mdi-account-tie",
        "Active": True,
        "NeedUser": True,
        "NeedStaff": True,
        "NeedDev": True,
        "NeedValidatedUser": True,
    },
]


def get_articles(user, category):
    """
    Permet de récupérer les articles de la catégorie en fonction des privilèges de l’utilisateur.
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
    Permet de récupérer les articles de la catégorie en fonction des privilèges de l’utilisateur.
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
    Permet de récupérer les articles de la catégorie en fonction des privilèges de l’utilisateur.
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
    Permet de récupérer les infos liées à la page courante pour l’user.
    :param user:
    :param page_name:
    :return:
    """
    if page_name not in page_info:
        return {}
    return {
            'extpages': get_ext_pages(user),
            "pages":  get_int_pages(user),
            "page_subtitle": page_info[page_name]["Title"],
            "page": page_name,
            "subpage": ""}
