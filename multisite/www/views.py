"""La page de view.py"""
from django.shortcuts import render
from . import settings
from .render_utils import get_page_data, get_articles


def index(request):
    """
    Définition de la page principale.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "news")
    articles = get_articles(request.user, 1)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        "data": {
            'derniers_articles': articles
        }
    })


def research(request):
    """
    Page de recherche.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "research")
    articles = get_articles(request.user, 2)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        "data": {
            'derniers_articles': articles
        }
    })


def projects(request):
    """
    Page des projets.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "projects")
    articles = get_articles(request.user, 3)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        "data": {
            'derniers_articles': articles
        }
    })


def links(request):
    """
    Page des liens
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "links")
    articles = get_articles(request.user, 4)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        "data": {
            'derniers_articles': articles
        }
    })
