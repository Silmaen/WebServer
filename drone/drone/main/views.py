"""main.views"""
from django.shortcuts import render
from .models import Article, DroneComponent, DroneConfiguration, DroneFlight


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
    df = DroneFlight.objects.order_by("-date")
    return render(request, "BaseFlight.html", {"page": "vols", "vols": df})


def configurations(request):
    """
    Main Page
    :param request: the page request
    :return: the redered page
    """
    dc = DroneConfiguration.objects.order_by('-version_number')
    return render(request, "BaseConfiguration.html", {"page": "confs", "configurations": dc})


def composants(request):
    """
    Main Page
    :param request: the page request
    :return: the redered page
    """
    dc = DroneComponent.objects.order_by("name")
    return render(request, "BaseComposants.html", {"page": "comps", "composants": dc})
