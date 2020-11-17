"""meteo.urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('summary', views.summary, name='summary'),
    path('desk', views.desk, name='desk'),
    path('station', views.station, name='station'),
]


#for page in views.subpages:
#    urlpatterns.append(path('/' + page["url"], page["fct"], page["name"]))
