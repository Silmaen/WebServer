"""main.views"""
from django.shortcuts import render
from .models import Article


def index(request):
    """
    Main Page
    :param request: the page request
    :return: the redered page
    """
    articles = Article.objects.order_by('-date')[:15]
    print(len(articles))
    return render(request, "BaseArticles.html", {"page": "news", "articles": articles})


def vols(request):
    """
    Main Page
    :param request: the page request
    :return: the redered page
    """
    return render(request, "base.html", {"page": "vols"})


def configurations(request):
    """
    Main Page
    :param request: the page request
    :return: the redered page
    """
    return render(request, "base.html", {"page": "confs"})


def composants(request):
    """
    Main Page
    :param request: the page request
    :return: the redered page
    """
    return render(request, "base.html", {"page": "comps"})
