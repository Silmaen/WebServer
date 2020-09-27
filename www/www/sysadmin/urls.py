"""news.urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('summary', views.summary, name='summary'),
    path('mlist', views.mlist, name='mlist'),
]
