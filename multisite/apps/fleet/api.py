"""The endpoints the machines and scripts talk to.

These are the contract `_common/ansible/roles/report/files/homelab-report` already
speaks, preserved path for path so the move off the Flask console needs nothing on
the machines beyond the port in the `report` role:

    POST /api/fleet/report/<machine>     Authorization: Bearer <REPORT_TOKEN>
    POST /api/fleet/approve/<machine>/<verb>
    GET  /api/fleet/state/

They authenticate with a shared bearer token, not with the session: the machines
POST straight to selene on the LAN, and a shell script on a timer cannot follow an
SSO redirect. That also keeps reporting alive while hestia and its proxy are down,
which is exactly when the reports are wanted.
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
    """The request body, including when it arrives chunked.

    `request.body` reads exactly `CONTENT_LENGTH` bytes, because that is all WSGI
    promises. A chunked request sends no `Content-Length`, so Django reads **zero
    bytes** and every parser downstream sees an empty document — whatever the
    Content-Type says.

    That is not a hypothetical: `uclient-fetch` is the only HTTP client on ceryx and
    eudore (no curl on either), and it sends `Transfer-Encoding: chunked` for both
    `--post-data` and `--post-file`, with no way to ask for a length. Captured off
    the wire:

        POST /api/fleet/report/ceryx HTTP/1.1
        Content-Type: application/json
        Transfer-Encoding: chunked

    gunicorn has already de-chunked the payload into `wsgi.input` by the time the
    view runs; it is only Django's length-bounded wrapper that refuses to read it.
    So fall through to the raw stream, and only when the normal path came back
    empty — reading `wsgi.input` after Django has consumed it would return nothing,
    which is exactly why this is a fallback rather than the first move.
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
    """Bearer-token endpoints, outside the session and outside the OIDC flow.

    `authentication_classes` is emptied on purpose: DRF's SessionAuthentication
    enforces CSRF, which a curl from a systemd timer cannot satisfy, and leaving
    the project's default `IsViewer` permission would demand a logged-in user.
    """

    authentication_classes = []
    permission_classes = []

    def token_ok(self, request):
        token = settings.FLEET_REPORT_TOKEN
        if not token:
            # An unset secret must never be read as "no secret required" — that is
            # how a misconfigured deploy starts accepting anything.
            return False
        return request.headers.get("Authorization") == f"Bearer {token}"


class ReportIngestView(TokenAuthenticatedView):
    def post(self, request, machine):
        if not settings.FLEET_REPORT_TOKEN:
            return Response(
                {"error": "REPORT_TOKEN n'est pas configuré sur la console"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if not self.token_ok(request):
            return Response({"error": "jeton invalide"}, status=status.HTTP_401_UNAUTHORIZED)

        # Sync first: a machine added to inventory.conf must be able to report
        # without waiting for someone to open the page.
        inventory.sync()
        target = Machine.objects.filter(name=machine, retired=False).first()
        if target is None:
            # Only names the inventory knows, which is what bounds this endpoint.
            return Response(
                {"error": f"{machine} n'est pas dans l'inventaire"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # request.body, not request.data: the callers here are shell scripts on
        # busybox, and content negotiation is not a hill worth dying on for an
        # ingestion endpoint with four known clients.
        #
        # `uclient-fetch` on the access points -- which have no curl -- sends
        # `application/x-www-form-urlencoded` whatever `--header` asks of it. DRF then
        # handed this view a QueryDict instead of the document and it answered 400;
        # a client sending no Content-Type at all got 415 before the view was reached.
        # Both on documents that were perfectly valid -- the same file POSTed with
        # curl answered 204. Flask never noticed, because `get_json(silent=True)`
        # falls back to the raw body.
        #
        # Reading the body directly also means DRF never runs its parsers, which is
        # what produced the 415.
        # utf-8-sig and not utf-8: hecate's agent builds its document with
        # PowerShell's `Set-Content -Encoding UTF8`, which writes a **byte-order
        # mark** -- the file starts EF BB BF -- and curl posts the bytes verbatim.
        # `json.loads` then fails on the leading ﻿. utf-8-sig strips a BOM when
        # there is one and is identical to utf-8 when there is not, so this costs
        # nothing for the other seven machines.
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
    """The same approval as the button, for scripts. Reuses the report token."""

    def post(self, request, machine, verb):
        if not self.token_ok(request):
            return Response({"error": "jeton invalide"}, status=status.HTTP_401_UNAUTHORIZED)
        error = ntfy.publish(verb, machine)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StateView(APIView):
    """The whole fleet as JSON — what `/api/state` served on the Flask console."""

    def get(self, request):
        return Response(as_json(build_state()))
