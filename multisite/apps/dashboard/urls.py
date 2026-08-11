"""Route de la vue d'ensemble de la console."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name='index'),
]
