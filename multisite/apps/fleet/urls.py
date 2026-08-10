from django.urls import path

from . import views

app_name = "fleet"

urlpatterns = [
    path("", views.FleetView.as_view(), name="index"),
    path("approve/<str:machine>/<str:verb>/", views.ApproveView.as_view(), name="approve"),
]
