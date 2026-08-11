"""Transforme un document `homelab-report` posté en lignes de base.

Séparé de la vue pour que la forme du document soit décrite en un seul endroit, et
pour qu'un document puisse être rejoué : chaque machine garde sa propre copie.
"""

import logging
from datetime import UTC, datetime

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Report, Stack

logger = logging.getLogger("apps.fleet")


class InvalidReportError(ValueError):
    """La charge reçue n'est pas un document homelab-report."""


def _parse_at(value):
    """`homelab-report` écrit `date -u '+%Y-%m-%dT%H:%M:%SZ'`."""
    parsed = parse_datetime(value) if isinstance(value, str) else None
    if parsed is None:
        try:
            parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except (TypeError, ValueError) as exc:
            raise InvalidReportError(f"horodatage illisible : {value!r}") from exc
    if timezone.is_naive(parsed):
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _behind(value):
    """La sonde écrit `-` quand elle ne peut pas savoir, ce qui n'est pas zéro."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def store(machine, payload):
    """Enregistre un rapport et réconcilie les stacks de la machine.

     :param machine : La machine déclarée qui a posté le document.
     :param payload : Le document décodé.
     :return : Le `Report` créé ou mis à jour.
    """
    if not isinstance(payload, dict) or "facts" not in payload:
        raise InvalidReportError("document homelab-report attendu")

    facts = payload.get("facts") or {}
    if not isinstance(facts, dict):
        raise InvalidReportError("`facts` doit être un objet")
    drift = payload.get("drift") or {}

    at = _parse_at(payload.get("at"))
    # update_or_create : reposter le même document est idempotent, le timer et un appel
    # manuel pouvant tous deux arriver.
    report, _ = Report.objects.update_or_create(
        machine=machine,
        at=at,
        defaults={
            "schema": payload.get("schema") or 1,
            "facts": facts,
            "drift_status": drift.get("status") or "unknown",
            "drift_count": drift.get("count") or 0,
            "drift_changes": drift.get("changes") or [],
        },
    )

    _store_stacks(machine, payload.get("stacks") or [])
    return report


def _store_stacks(machine, stacks):
    """Crée ou met à jour les stacks déployées de la machine.

    Rien n'est supprimé : une stack qui cesse d'être rapportée garde sa ligne et son
    `last_seen` vieillit, ce qui est la réponse honnête — « ceci était déployé ici »
    est une information, une ligne qui disparaît en silence non.
    """
    now = timezone.now()
    for entry in stacks:
        if not isinstance(entry, dict):
            continue
        project = (entry.get("project") or "").strip()
        path = (entry.get("path") or "").strip()
        if not project or not path:
            continue
        Stack.objects.update_or_create(
            machine=machine,
            project=project,
            path=path,
            defaults={
                "remote": entry.get("remote") or "",
                "head": entry.get("head") or "",
                "worktree": entry.get("worktree") or "",
                "behind": _behind(entry.get("behind")),
                "compose": entry.get("compose") or Stack.Compose.UNKNOWN,
                "last_seen": now,
            },
        )
