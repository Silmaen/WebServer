"""Fichier main.urls.py définissant les urls."""
from django.urls import path
from .views import *


urlpatterns = [
    path("", index),
    path('ayoaron', index, name='index'),
]
