"""Lit `_common/inventory.conf` et le reflète dans les lignes `Machine`.

Ce fichier est la liste de machines unique de tout le lab (le routeur le lit en
busybox awk, ansible en dérive son inventaire), donc ce module ne fait que le lire :
une machine n'est jamais créée ici, et une ligne qui ne correspond plus au fichier
est réconciliée.

Format (séparé par des espaces, `#` commence un commentaire, `-` signifie
« sans objet »)  :

    name  ip  mac  role  os  ac  wol  order  ssh
"""

import logging
from pathlib import Path

from django.conf import settings

from .models import Machine

logger = logging.getLogger("apps.fleet")

COLUMNS = ("name", "ip", "mac", "role", "os", "ac", "wol", "order", "ssh")

# Les champs que `sync()` écrit, depuis les noms de colonnes du fichier. Gardés comme
# données pour que la comparaison ne puisse pas s'écarter de l'affectation.
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
    """`-` signifie « sans objet » dans ce fichier, pas la chaîne littérale."""
    if column == "ip":
        return None if value == "-" else value
    if column == "order":
        try:
            return int(value)
        except ValueError:
            return 0
    return "" if value == "-" else value


def parse(path=None):
    """Les machines dont la console parle, dans l'ordre du fichier.

    Les machines sans compte ssh sont ignorées : rien ne rapporte pour l'imprimante
    ou la box, donc leur ligne resterait à « never reported » pour toujours et
    apprendrait à ignorer la colonne.
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
    """Réconcilie `Machine` avec le fichier. Rend le compte de ce qui a été fait.

    N'écrit que les lignes qui diffèrent réellement : appelée à chaque rapport et à
    chaque affichage de page, une opération nulle doit vraiment être nulle, sinon
    `updated_at` ne veut plus rien dire.
    """
    rows = parse(path)
    if not rows:
        # Un fichier illisible ou vide ne doit pas retirer toute la flotte : un montage
        # manquant est une erreur de déploiement, pas une décision.
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
        logger.info(
            "inventaire synchronisé : %d créés, %d mis à jour, %d retirés",
            created, updated, retired,
        )
    return {"created": created, "updated": updated, "retired": retired, "seen": len(seen)}
