"""Mounted under `/api/fleet/` — see `apps/fleet/api.py` for why these are
bearer-token endpoints and not session ones."""

from django.urls import path

from . import api

app_name = "fleet-api"

urlpatterns = [
    path("report/<str:machine>", api.ReportIngestView.as_view(), name="report"),
    path("approve/<str:machine>/<str:verb>", api.ApproveApiView.as_view(), name="approve"),
    path("state/", api.StateView.as_view(), name="state"),
]
