"""Fichier main.urls.py définissant les urls."""
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings as main_settings
from django.urls import path, include
from .views import *


urlpatterns = [
    path("", potager, name='index'),
    path('potager/', potager, name='potager'),
    path('potager/<int:row>/<int:col>', potager_detail, name='potager_detail'),
    path('semis/', semis, name='semis'),
    path('semis/<int:id>', semis_detail, name='semis_detail'),
    path('plants/', potager_plants, name='potager_plant'),
    path('plants/<int:id>', potager_plants_details, name='potager_plants_details'),
    path('netadmin/', include('www_netadmin.urls')),
] + static(main_settings.MEDIA_URL, document_root=main_settings.MEDIA_ROOT)