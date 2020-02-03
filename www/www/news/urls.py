from django.urls import path
from django.conf.urls import url,include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('resarch',views.resarch),
    path('projects',views.projects),
    path('links',views.links),
]
