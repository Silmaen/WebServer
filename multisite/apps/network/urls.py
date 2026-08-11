"""Routes des pages réseau et des identifiants de passerelle."""

from django.urls import path

from . import views

app_name = "network"

urlpatterns = [
    path("", views.NetworkListView.as_view(), name='list'),
    path("add/", views.NetworkCreateView.as_view(), name='create'),
    path("<uuid:pk>/", views.NetworkDetailView.as_view(), name='detail'),
    path("<uuid:pk>/edit/", views.NetworkUpdateView.as_view(), name='update'),
    path("<uuid:pk>/delete/", views.NetworkDeleteView.as_view(), name='delete'),
    path("<uuid:pk>/scan/", views.NetworkScanView.as_view(), name='scan'),
    # Identifiants de passerelle
    path("credentials/", views.GatewayCredentialListView.as_view(), name='credential-list'),
    path("credentials/add/", views.GatewayCredentialCreateView.as_view(), name='credential-create'),
    path(
        "credentials/<uuid:pk>/edit/",
        views.GatewayCredentialUpdateView.as_view(), name='credential-update',
    ),
    path(
        "credentials/<uuid:pk>/delete/",
        views.GatewayCredentialDeleteView.as_view(), name='credential-delete',
    ),
    path(
        "credentials/<uuid:pk>/test/",
        views.GatewayCredentialTestView.as_view(), name='credential-test',
    ),
]
