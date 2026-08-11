"""Les endpoints auxquels les machines et les scripts s'adressent.

Contrat déjà parlé par `homelab-report`, préservé chemin pour chemin :

    POST /api/fleet/report/<machine>     Authorization: Bearer <REPORT_TOKEN>
    POST /api/fleet/approve/<machine>/<verb>
    GET  /api/fleet/state/

Ils s'authentifient par jeton partagé et non par session : un script shell sur un
timer ne peut pas suivre une redirection SSO, et cela garde les rapports vivants
quand le proxy est en panne — précisément le moment où on les veut.
"""

import json
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import inventory, ntfy
from .ingest import InvalidReportError, store
from .models import Machine
from .state import as_json, build_state

logger = logging.getLogger("apps.fleet")


def _raw_body(request):
    """Le corps de la requête, y compris quand il arrive en chunked.

    `request.body` ne lit que `CONTENT_LENGTH` octets, or une requête chunked n'en
    déclare aucun : Django lit alors zéro octet. C'est le cas de `uclient-fetch`,
    seul client HTTP des points d'accès. gunicorn a déjà déchunké la charge dans
    `wsgi.input`, d'où ce repli — seulement en repli, car lire le flux après Django
    ne rendrait rien.
    """
    body = request.body
    if body:
        return body
    stream = request.META.get("wsgi.input")
    if stream is None:
        return b""
    try:
        return stream.read()
    except (OSError, ValueError):
        return b""


class TokenAuthenticatedView(APIView):
    """Endpoints à jeton porteur, hors session et hors flux OIDC.

    `authentication_classes` est vidé à dessein : la SessionAuthentication de DRF
    impose le CSRF, qu'un curl lancé par un timer systemd ne peut pas satisfaire.
    """

    authentication_classes = []
    permission_classes = []

    def token_ok(self, request):
        """Le jeton porteur présenté est-il le bon ?"""
        token = settings.FLEET_REPORT_TOKEN
        if not token:
            # Un secret non configuré ne doit jamais se lire « aucun secret requis ».
            return False
        return request.headers.get("Authorization") == f"Bearer {token}"


class ReportIngestView(TokenAuthenticatedView):
    """Réception d'un document `homelab-report` posté par une machine."""

    def post(self, request, machine):
        """Valide le jeton et le nom de la machine, puis enregistre le document."""
        if not settings.FLEET_REPORT_TOKEN:
            return Response(
                {"error": "REPORT_TOKEN n'est pas configuré sur la console"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if not self.token_ok(request):
            return Response({"error": "jeton invalide"}, status=status.HTTP_401_UNAUTHORIZED)

        # Synchroniser d'abord : une machine ajoutée à inventory.conf doit pouvoir
        # rapporter sans attendre que quelqu'un ouvre la page.
        inventory.sync()
        target = Machine.objects.filter(name=machine, retired=False).first()
        if target is None:
            # Seuls les noms connus de l'inventaire, ce qui borne cet endpoint.
            return Response(
                {"error": f"{machine} n'est pas dans l'inventaire"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Le corps brut et non `request.data` : les appelants sont des scripts shell
        # dont le Content-Type est faux ou absent, ce qui faisait répondre 400 ou 415
        # sur des documents valides. utf-8-sig, car l'agent Windows écrit un BOM.
        try:
            payload = json.loads(_raw_body(request).decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return Response(
                {"error": f"corps de requête illisible : {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            store(target, payload)
        except InvalidReportError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ApproveApiView(TokenAuthenticatedView):
    """La même approbation que le bouton, pour les scripts. Réutilise le jeton de rapport."""

    def post(self, request, machine, verb):
        """Publie l'approbation demandée sur le sujet ntfy."""
        if not self.token_ok(request):
            return Response({"error": "jeton invalide"}, status=status.HTTP_401_UNAUTHORIZED)
        error = ntfy.publish(verb, machine)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StateView(APIView):
    """Toute la flotte en JSON — ce que servait `/api/state` sur la console Flask."""

    def get(self, request):
        """Rend l'état assemblé de la flotte."""
        return Response(as_json(build_state()))
