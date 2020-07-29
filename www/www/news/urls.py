"""news.urls"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('research', views.research),
    path('projects', views.projects),
    path('links', views.links),
    path('sysadmin', views.sysadmin_base),
    path('sysadmin/<str:name>', views.sysadmin),
]
