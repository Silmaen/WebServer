"""What wud knows about newer image tags.

Not reimplemented here on purpose: asking a registry whether a newer tag exists is
a solved problem with real edge cases (tag patterns, digests, private registries),
and wud already runs next to this app on selene.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger("apps.fleet")


def containers():
    """Ask wud what it watches. Returns `(list, error)`.

    A wud that is down must never take the page with it: the fleet table is most
    wanted precisely when something is broken.
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
    """Group wud's view per machine.

    wud names its local watcher `local`; every other watcher is named after the
    machine it points at, through the read-only docker proxy that
    `_common/monitoring_agent` runs on port 2378. So the watcher name *is* the
    machine name, except for the one looking at its own socket.
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
