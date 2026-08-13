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
    # Par clé et non par machine + projet : une stack déplacée porte le même projet à
    # deux chemins, et c'est justement la ligne d'avant qu'il s'agit d'oublier.
    path(
        "stacks/<uuid:pk>/oublier/",
        views.ForgetStackView.as_view(), name='forget_stack',
    ),
    path(
        "stacks/oublier-disparues/",
        views.ForgetGoneStacksView.as_view(), name='forget_gone_stacks',
    ),
]
