"""main.views"""
from django.shortcuts import render, redirect
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


def register(request):
    good = True
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse("news"))
        good = False
    return render(request, "users/register.html",{"form": CustomUserCreationForm, "isgood": good})
