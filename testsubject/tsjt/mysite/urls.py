"""mysite.urls"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('article/<int:id>-<slug:slug>', views.lire, name='lire'),
    path('about', views.about),
    path('blog', views.blog),
    path('media', views.media),
]
