"""La definition des vues"""
from django.shortcuts import render
from . import settings


def index(request):
    """La toute première page"""
    return render(request, "ayoaron/base.html", settings.base_info)
