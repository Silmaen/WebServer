"""Ce que wud sait des tags d'images plus récents.

Volontairement non réimplémenté : interroger un registre est un problème résolu, avec
de vrais cas limites (motifs de tags, digests, registres privés), et wud tourne déjà
à côté de cette app.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger("apps.fleet")


def containers():
    """Demande à wud ce qu'il surveille. Rend `(liste, erreur)`.

    Un wud en panne ne doit jamais emporter la page : le tableau de la flotte est
    justement le plus attendu quand quelque chose est cassé.
    """
    url = f"{settings.FLEET_WUD_URL.rstrip('/')}/api/containers"
    try:
        answer = requests.get(url, timeout=8)
        answer.raise_for_status()
        return answer.json(), None
    except (requests.RequestException, ValueError) as exc:
        logger.warning("wud injoignable (%s) : %s", url, exc)
        return [], str(exc)


def by_machine(raw):
    """Groupe la vue de wud par machine.

    wud nomme son watcher local `local` ; tous les autres portent le nom de la machine
    qu'ils visent. Le nom du watcher *est* donc le nom de la machine, sauf pour celui
    qui regarde sa propre socket.
    """
    grouped = {}
    for container in raw:
        watcher = container.get("watcher") or "?"
        machine = "selene" if watcher == "local" else watcher
        entry = grouped.setdefault(machine, {"total": 0, "behind": []})
        entry["total"] += 1
        if container.get("updateAvailable"):
            image = container.get("image") or {}
            entry["behind"].append(
                {
                    "container": container.get("name", "?"),
                    "image": image.get("name") or "?",
                    "tag": (image.get("tag") or {}).get("value") or "?",
                    "available": (container.get("result") or {}).get("tag") or "?",
                }
            )
    return grouped
