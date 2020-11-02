"""main.views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.urls import reverse
from .models import *
from .forms import *


def index(request):
    """
    Main Page
    :param request: the page request
    :return: the rendered page
    """
    if request.user.is_authenticated:
        articles = Article.objects.order_by('-date')[:15]
        return render(request, "BaseArticles.html", {"page": "news", "articles": articles})
    else:
        return render(request, "BaseArticles.html", {"page": "news", "articles": []})


def detailed_article(request, article_id):
    """
    page for one article with details
    :param request: the page request
    :param article_id: the id of the article to find
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    article = get_object_or_404(Article, pk=article_id)
    return render(request, "DetailedArticle.html", {"page": "news", "article": article})


def vols(request):
    """
    Main Page
    :param request: the page request
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    df = DroneFlight.objects.order_by("-date")
    return render(request, "BaseFlight.html", {"page": "vols", "vols": df})


def detailed_vol(request, vol_id):
    """
    page for one article with details
    :param request: the page request
    :param vol_id: the id of the flight to find
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    vol = get_object_or_404(DroneFlight, pk=vol_id)
    return render(request, "DetailedFlight.html", {"page": "news", "vol": vol})


def configurations(request):
    """
    Main Page
    :param request: the page request
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    dc = DroneConfiguration.objects.order_by('-version_number')
    return render(request, "BaseConfiguration.html", {"page": "confs", "configurations": dc})


def detailed_configuration(request, configurtion_id):
    """
    page for one article with details
    :param request: the page request
    :param configurtion_id: the id of the article to find
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    dc = get_object_or_404(DroneConfiguration, pk=configurtion_id)
    return render(request, "DetailedConfiguration.html", {"page": "confs", "configuration": dc})


def composants(request):
    """
    Main Page
    :param request: the page request
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    dc = DroneComponent.objects.order_by("name")
    return render(request, "BaseComposants.html", {"page": "comps", "composants": dc})


def detailed_composant(request, comp_id):
    """
    page for one article with details
    :param request: the page request
    :param comp_id: the id of the article to find
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    dc = get_object_or_404(DroneComponent, pk=comp_id)
    return render(request, "DetailedComposant.html", {"page": "comps", "comp": dc})


def register(request):
    good = True
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse("news"))
        good = False
    return render(request, "users/register.html", {"form": CustomUserCreationForm, "isgood": good})
