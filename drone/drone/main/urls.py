"""main.urls"""
from django.urls import path
from django.conf.urls import include, url
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('news', views.index, name='news'),
    path('vols', views.vols, name='vols'),
    path('confs', views.configurations, name='confs'),
    path('comps', views.composants, name='comps'),
    url(r"^accounts/", include("django.contrib.auth.urls")),
    url(r"^register/", views.register, name="register"),

]
