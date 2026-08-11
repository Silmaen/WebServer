"""Route de la page de supervision."""

from django.urls import path

from . import views

app_name = "monitoring"

urlpatterns = [
    path("", views.MonitoringDashboardView.as_view(), name='dashboard'),
]
