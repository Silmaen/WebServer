"""meteo.urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('summary', views.summary, name='meteo'),
    path('desk', views.desk, name='desk'),
    path('station', views.station, name='station'),
]
