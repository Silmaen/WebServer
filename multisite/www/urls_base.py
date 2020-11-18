"""Fichier main.urls.py définissant les urls."""
from .urls import urlpatterns as local_patterns
from django.contrib import admin
from django.urls import path, include

urlpatterns = local_patterns + [
    # Include for the system
    path('profile/', include('connector.urls')),
    path('admin/', admin.site.urls),
    path('markdownx/', include('markdownx.urls')),  # Pour le décodage de Markdown.
]
