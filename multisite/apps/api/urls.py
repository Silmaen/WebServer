"""Routes JSON de la console, montées sous `/api/`."""

from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("health/", views.HealthCheckView.as_view(), name='health'),
    path(
        "monitoring/timeseries/",
        views.MonitoringTimeSeriesView.as_view(), name='monitoring-timeseries',
    ),
    path("devices/", views.DeviceListAPIView.as_view(), name='device-list'),
]
