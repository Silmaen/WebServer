"""Fichier main.urls.py définissant les urls."""
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings as main_settings
from django.urls import path, include
from .views import index, news_page, detailed_news, research, projects, links


urlpatterns = [
    path("", index),
    path('www/', index, name='index'),
    path('www/<int:n_page>', news_page, name='news_page'),
    path('news/<int:article_id>', detailed_news, name='detailed_news'),
    path('research', research, name='research'),
    path('projects', projects, name='projects'),
    path('links', links, name='links'),
] + static(main_settings.MEDIA_URL, document_root=main_settings.MEDIA_ROOT)
