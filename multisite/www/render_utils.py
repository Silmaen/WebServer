"""
gathering functions to render pages
"""
from .models import Article
from common.user_utils import user_is_developper, user_is_validated

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
        "name": "Ayoaron",
        "url": "https://ayoaron.argawaen.net",
        "icon": "",
        "Active": False,  # TODO: reactivate this site
        "NeedUser": False,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": False,
     },
    {
        "name": "Drone",
        "url": "https://drone.argawaen.net",
        "icon": "",
        "Active": True,
        "NeedUser": False,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": True,
     },
    {
        "name": "TestSubject",
        "url": "https://testsubject.argawaen.net",
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
    "netadmin": {
        "Title": "Administration machines",
    },
    "meteo": {
        "Title": "Relevés Météo",
    }
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
        "name": "Meteo",
        "url": "meteo",
        "icon": "mdi-weather-windy-variant",
        "Active": True,
        "NeedUser": True,
        "NeedStaff": False,
        "NeedDev": False,
        "NeedValidatedUser": True,
    },
    {
        "name": "Network admin",
        "url": "netadmin",
        "icon": "mdi-cctv",
        "Active": True,
        "NeedUser": True,
        "NeedStaff": True,
        "NeedDev": True,
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
