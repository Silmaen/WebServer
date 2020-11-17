"""news.urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('etat', views.summary, name='etat'),
    path('mlist', views.mlist, name='mlist'),
]
