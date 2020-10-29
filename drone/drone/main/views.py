"""main.views"""
from django.shortcuts import render


def index(request):
    """
    Main Page
    :param request: the page request
    :return: the redered page
    """
    return render(request, "base.html", {"page": "news"})


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
