from django.urls import path
from . import views

app_name = "devices"

urlpatterns = [
    path("", views.DeviceListView.as_view(), name="list"),
    path("add/", views.DeviceCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.DeviceDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.DeviceUpdateView.as_view(), name="update"),
    path("<uuid:pk>/delete/", views.DeviceDeleteView.as_view(), name="delete"),
    path("<uuid:pk>/probe/", views.DeviceProbeView.as_view(), name="probe"),
]
