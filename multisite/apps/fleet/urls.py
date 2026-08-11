"""Routes des pages de la flotte."""

from django.urls import path

from . import views

app_name = "fleet"

urlpatterns = [
    path("", views.FleetView.as_view(), name='index'),
    path("stacks/", views.StacksView.as_view(), name='stacks'),
    path("approve/<str:machine>/<str:verb>/", views.ApproveView.as_view(), name='approve'),
    path(
        "deploy/<str:machine>/<str:project>/",
        views.DeployStackView.as_view(), name='deploy',
    ),
]
