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
    # Par clé et non par machine + projet : un refactor laisse plusieurs lignes au même
    # projet à des chemins différents, et c'est une ligne précise qu'il s'agit de retirer.
    path(
        "stacks/<uuid:pk>/supprimer/",
        views.DeleteStackView.as_view(), name='delete_stack',
    ),
    path(
        "stacks/supprimer-disparues/",
        views.DeleteGoneStacksView.as_view(), name='delete_gone_stacks',
    ),
    path(
        "stacks/<uuid:pk>/ignorer/",
        views.AckStackAlertView.as_view(), name='ack_stack_alert',
    ),
]
