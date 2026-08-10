"""Publishing an approval — the console's only way to affect a machine.

Worth stating plainly, because it is what lets this page sit behind nothing more
than SSO: **no command is ever transmitted.** The console writes a message naming
one of four verbs to an ntfy topic it can write and not read. The machine's own
agent decides which of its playbooks that verb means, and a reboot additionally
needs the machine's own recipe to allow one.

So the worst an attacker who reaches this endpoint can do is ask a machine to
converge to the state its git checkout already describes.
"""

import logging

import requests
from django.conf import settings

from .models import Machine

logger = logging.getLogger("apps.fleet")

VERBS = ("converge", "upgrade", "upgrade-reboot", "report")

VERB_LABELS = {
    "converge": "Converger",
    "upgrade": "Mettre à jour",
    "upgrade-reboot": "Mettre à jour + redémarrer",
    "report": "Demander un rapport",
}


def publish(verb, machine_name):
    """Publish one approval. Returns `None` on success, or a message to show."""
    if verb not in VERBS:
        return f"action inconnue : {verb!r}"
    # Only names the inventory knows. This is what makes `../..` in a machine name
    # impossible rather than merely unlikely.
    if not Machine.objects.filter(name=machine_name, retired=False).exists():
        return f"{machine_name} n'est pas dans l'inventaire"
    if not settings.FLEET_NTFY_TOKEN:
        # Refusing is the safe failure. An unset token must not be read as "no
        # token required", which is how a misconfigured deploy starts publishing.
        return "NTFY_TOKEN n'est pas configuré sur la console"

    url = f"{settings.FLEET_NTFY_URL.rstrip('/')}/{settings.FLEET_NTFY_TOPIC}"
    try:
        answer = requests.post(
            url,
            data=f"{verb} {machine_name}".encode(),
            headers={
                "Authorization": f"Bearer {settings.FLEET_NTFY_TOKEN}",
                "Title": f"{machine_name}: {verb}",
                "Tags": "house",
            },
            timeout=10,
        )
        answer.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("publication ntfy impossible (%s) : %s", url, exc)
        return f"publication ntfy impossible : {exc}"

    logger.info("approbation publiée : %s %s", verb, machine_name)
    return None
