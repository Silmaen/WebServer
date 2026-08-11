"""Publier une approbation — le seul moyen qu'a la console d'agir sur une machine.

**Aucune commande n'est jamais transmise** : la console écrit un message nommant
l'un des quatre verbes sur un sujet ntfy qu'elle peut écrire et non lire, et c'est
l'agent de la machine qui décide du playbook correspondant. Le pire qu'un attaquant
atteignant cet endpoint puisse faire est de demander à une machine de converger vers
l'état que son dépôt git décrit déjà.
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
    """Publie une approbation.

     :param verb : L'un des quatre verbes de `VERBS`.
     :param machine_name : Le nom d'une machine de l'inventaire.
     :return : None en cas de succès, sinon le message à afficher.
    """
    if verb not in VERBS:
        return f"action inconnue : {verb!r}"
    # Seuls les noms connus de l'inventaire : c'est ce qui rend un `../..` dans un nom
    # de machine impossible plutôt que simplement improbable.
    if not Machine.objects.filter(name=machine_name, retired=False).exists():
        return f"{machine_name} n'est pas dans l'inventaire"
    if not settings.FLEET_NTFY_TOKEN:
        # Refuser est l'échec sûr : un jeton non configuré ne doit pas se lire
        # « aucun jeton requis ».
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
