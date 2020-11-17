"""Fichier main.urls.py définissant les urls."""
from django.conf.urls.static import static
from django.conf import settings as main_settings
from django.urls import path
from .views import *


urlpatterns = [
    path("", index, name='index'),
    path('tsjt/', index, name='index1'),
    path('article/<int:id>-<slug:slug>', lire, name='lire'),
    path('about', about, name='about'),
    path('blog', blog, name='blog'),
    path('medium', media, name='media'),
] + static(main_settings.MEDIA_URL, document_root=main_settings.MEDIA_ROOT)
