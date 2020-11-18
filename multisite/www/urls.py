"""Fichier main.urls.py définissant les urls."""
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings as main_settings
from django.urls import path, include
from .views import *


urlpatterns = [
    path("", index),
    path('www/', index, name='index'),
    path('research', research, name='research'),
    path('projects', projects, name='projects'),
    path('links', links, name='links'),
    path('meteo/', include('www_meteo.urls')),
    path('netadmin/', include('www_netadmin.urls')),
] + static(main_settings.MEDIA_URL, document_root=main_settings.MEDIA_ROOT)
