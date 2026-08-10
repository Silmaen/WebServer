"""Turn one posted `homelab-report` document into rows.

Kept apart from the view so the shape of the document is described in one place,
and so a document can be replayed (a machine keeps its own copy in
`/var/lib/homelab/report.json`, which the Flask console had no way to backfill).
"""

import logging
from datetime import UTC, datetime

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Report, Stack

logger = logging.getLogger("apps.fleet")


class InvalidReportError(ValueError):
    """The payload is not a homelab-report document."""


def _parse_at(value):
    """`homelab-report` writes `date -u '+%Y-%m-%dT%H:%M:%SZ'`."""
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
    """The probe writes `-` when it cannot tell, which is not zero."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def store(machine, payload):
    """Store a report and reconcile the machine's stacks. Returns the `Report`."""
    if not isinstance(payload, dict) or "facts" not in payload:
        raise InvalidReportError("document homelab-report attendu")

    facts = payload.get("facts") or {}
    if not isinstance(facts, dict):
        raise InvalidReportError("`facts` doit être un objet")
    drift = payload.get("drift") or {}

    at = _parse_at(payload.get("at"))
    # update_or_create, so re-posting the same document is idempotent: the timer and
    # a manual `homelab-report` run can both land without creating a duplicate.
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
    """Upsert the machine's deployed stacks.

    Nothing is deleted. A stack that stops being reported keeps its row and its
    `last_seen` goes stale, which is the honest answer — "this used to be deployed
    here" is information, and a row silently disappearing is not.
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
