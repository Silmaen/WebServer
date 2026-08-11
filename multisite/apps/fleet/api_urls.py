"""Routes montées sous `/api/fleet/`.

Voir `apps/fleet/api.py` pour la raison de leur authentification par jeton porteur
plutôt que par session.
"""

from django.urls import path

from . import api

app_name = "fleet-api"

urlpatterns = [
    path("report/<str:machine>", api.ReportIngestView.as_view(), name='report'),
    path("approve/<str:machine>/<str:verb>", api.ApproveApiView.as_view(), name='approve'),
    path("state/", api.StateView.as_view(), name='state'),
]
