"""Fichier main.urls.py définissant les urls."""
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings as main_settings
from django.urls import path, include
from .views import *


urlpatterns = [
    path("", index),
    path('tsjt/', index, name='index'),
    path('article/<int:id>-<slug:slug>', lire, name='lire'),
    path('about', about),
    path('blog', blog),
    path('medium', media),
    path('admin/', admin.site.urls),
    path('markdownx/', include('markdownx.urls')),  # Pour le décodage de Markdown.
] + static(main_settings.MEDIA_URL, document_root=main_settings.MEDIA_ROOT)
