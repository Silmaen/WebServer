"""Read `_common/inventory.conf` and mirror it into `Machine` rows.

The file is the single machine list of the whole lab: `homelab-wake` parses it on
the router with busybox awk, ansible's dynamic inventory translates it, and
`homelab-status.sh` walks it. So this module only ever reads it — a machine is
never created here, and a row that no longer matches the file is reconciled, not
kept.

Format (whitespace separated, `#` starts a comment, `-` means not applicable):

    name  ip  mac  role  os  ac  wol  order  ssh
"""

import logging
from pathlib import Path

from django.conf import settings

from .models import Machine

logger = logging.getLogger("apps.fleet")

COLUMNS = ("name", "ip", "mac", "role", "os", "ac", "wol", "order", "ssh")

# The fields `sync()` writes, mapped from the file's column names. Kept as data so
# the comparison below cannot drift from the assignment.
FIELDS = {
    "ip": "ip",
    "mac": "mac",
    "role": "role",
    "os": "os_family",
    "ac": "ac_restores",
    "wol": "wol_known",
    "order": "wake_order",
    "ssh": "ssh_user",
}


def _clean(column, value):
    """`-` means "not applicable" in this file, not the literal string."""
    if column == "ip":
        return None if value == "-" else value
    if column == "order":
        try:
            return int(value)
        except ValueError:
            return 0
    return "" if value == "-" else value


def parse(path=None):
    """The machines the console is about, in file order.

    Machines with no ssh login are skipped, exactly as the Flask console skipped
    them: nothing reports for the printer or the ISP box, so a row for them would
    sit at `never reported` for ever and teach you to ignore the column.
    """
    path = Path(path or settings.FLEET_INVENTORY)
    if not path.is_file():
        logger.warning("inventaire introuvable : %s", path)
        return []

    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) < len(COLUMNS):
            continue
        row = dict(zip(COLUMNS, fields, strict=False))
        if row["ssh"] == "-":
            continue
        rows.append(row)
    return rows


def sync(path=None):
    """Reconcile `Machine` with the file. Returns what it did.

    Only writes rows that actually differ. This is called on every report POST and
    on every page render — reading ten lines of text is cheaper than any staleness
    bug — so a no-op has to really be a no-op, or the table's `updated_at` becomes
    meaningless and every run looks like a change.
    """
    rows = parse(path)
    if not rows:
        # An unreadable or empty file must not retire the whole fleet. A missing
        # mount is a deployment error, not a decision to forget every machine.
        return {"created": 0, "updated": 0, "retired": 0, "seen": 0}

    seen, created, updated = set(), 0, 0
    for row in rows:
        name = row["name"]
        seen.add(name)
        values = {field: _clean(column, row[column]) for column, field in FIELDS.items()}
        values["retired"] = False

        machine, was_created = Machine.objects.get_or_create(name=name, defaults=values)
        if was_created:
            created += 1
            continue
        changed = [f for f, v in values.items() if getattr(machine, f) != v]
        if changed:
            for field in changed:
                setattr(machine, field, values[field])
            machine.save(update_fields=[*changed, "updated_at"])
            updated += 1

    retired = Machine.objects.filter(retired=False).exclude(name__in=seen).update(retired=True)
    if created or updated or retired:
        logger.info("inventaire synchronisé : %d créés, %d mis à jour, %d retirés", created, updated, retired)
    return {"created": created, "updated": updated, "retired": retired, "seen": len(seen)}
