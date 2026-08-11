"""Publier une approbation — le seul moyen qu'a la console d'agir sur une machine.

**Aucune commande n'est jamais transmise** : la console écrit un verbe et des noms
qu'elle a d'abord validés en base, sur un sujet ntfy qu'elle peut écrire et non lire.
C'est l'agent de la machine qui décide du playbook ou du script correspondant. Le pire
qu'un attaquant atteignant cet endpoint puisse faire est de demander à une machine de
converger vers l'état que son dépôt git décrit déjà.
"""

import logging

import requests
from django.conf import settings

from .models import Machine, Stack

logger = logging.getLogger("apps.fleet")

VERBS = ("converge", "upgrade", "upgrade-reboot", "report")

VERB_LABELS = {
    "converge": "Converger",
    "upgrade": "Mettre à jour",
    "upgrade-reboot": "Mettre à jour + redémarrer",
    "report": "Demander un rapport",
}

# Verbe des stacks, tenu à part de VERBS : celui-ci porte un second nom et n'a donc
# pas sa place parmi les boutons par machine de la page Flotte.
DEPLOY_VERB = "deploy"


def _post(corps, titre):
    """Publie un message sur le sujet ntfy. Rend None, ou le message à afficher."""
    if not settings.FLEET_NTFY_TOKEN:
        # Refuser est l'échec sûr : un jeton non configuré ne doit pas se lire
        # « aucun jeton requis ».
        return "NTFY_TOKEN n'est pas configuré sur la console"

    url = f"{settings.FLEET_NTFY_URL.rstrip('/')}/{settings.FLEET_NTFY_TOPIC}"
    try:
        answer = requests.post(
            url,
            data=corps.encode(),
            headers={
                "Authorization": f"Bearer {settings.FLEET_NTFY_TOKEN}",
                "Title": titre,
                "Tags": "house",
            },
            timeout=10,
        )
        answer.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("publication ntfy impossible (%s) : %s", url, exc)
        return f"publication ntfy impossible : {exc}"
    return None


def _machine_connue(machine_name):
    """La machine est-elle dans l'inventaire ?

    Seuls les noms connus sont publiés : c'est ce qui rend un `../..` dans un nom
    impossible plutôt que simplement improbable.
    """
    return Machine.objects.filter(name=machine_name, retired=False).exists()


def publish(verb, machine_name):
    """Publie une approbation pour une machine.

     :param verb : L'un des quatre verbes de `VERBS`.
     :param machine_name : Le nom d'une machine de l'inventaire.
     :return : None en cas de succès, sinon le message à afficher.
    """
    if verb not in VERBS:
        return f"action inconnue : {verb!r}"
    if not _machine_connue(machine_name):
        return f"{machine_name} n'est pas dans l'inventaire"

    erreur = _post(f"{verb} {machine_name}", f"{machine_name}: {verb}")
    if erreur:
        return erreur
    logger.info("approbation publiée : %s %s", verb, machine_name)
    return None


def publish_deploy(machine_name, project):
    """Demande la mise à jour d'une stack via son script de déploiement.

    Le corps publié est `deploy <machine> <projet>` : deux noms, jamais un chemin.
    L'agent de la machine retrouve lui-même le script à partir du projet, exactement
    comme il retrouve un playbook à partir d'un verbe.

     :param machine_name : Le nom d'une machine de l'inventaire.
     :param project : Le projet compose d'une stack déployable de cette machine.
     :return : None en cas de succès, sinon le message à afficher.
    """
    if not _machine_connue(machine_name):
        return f"{machine_name} n'est pas dans l'inventaire"

    stack = Stack.objects.filter(machine__name=machine_name, project=project).first()
    if stack is None:
        return f"{project} n'est pas une stack connue de {machine_name}"
    # La sonde est seule à savoir si un script existe : sans elle, on ne demande rien.
    if not stack.deployable:
        return f"{project} n'a pas de script de déploiement exploitable"

    erreur = _post(
        f"{DEPLOY_VERB} {machine_name} {project}",
        f"{machine_name}: {DEPLOY_VERB} {project}",
    )
    if erreur:
        return erreur
    logger.info("déploiement demandé : %s/%s", machine_name, project)
    return None
