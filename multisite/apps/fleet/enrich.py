"""Joindre les machines saisies dans `www` à ce que la flotte sait d'elles.

La page de monitoring du site garde sa structure — les `ServiceCategorie`, avec leurs
machines et leurs serveurs, telles que tu les as saisies. Ce module lui ajoute ce que
les machines rapportent d'elles-mêmes et qu'aucune saisie ne pourrait tenir à jour :
uptime, mises à jour en attente, dérive ansible, images en retard, stacks déployées.

Deux principes, pour éviter les doublons que cette fusion est censée supprimer :

* **on ne réassemble rien.** `apps.fleet.state.build_state()` sait déjà agréger les
  rapports, wud et l'inventaire ; on lui demande le résultat et on le raccroche. Un
  assembleur, deux consommateurs.
* **l'état en ligne est dérivé, pas stocké.** `www.Machine.en_ligne` était écrit par
  `www.tasks.verifier_machines`, c'est-à-dire par le second moteur de checks. Le lire
  ici depuis le rapport et le scanner évite d'avoir deux écrivains pour un même fait —
  et c'est ce qui permet de débrancher ce moteur sans figer la page.

L'appariement se fait sur l'adresse d'abord, sur le nom ensuite : `inventory.conf` est
la référence pour les adresses, alors que les noms saisis varient (`hermes` contre
`hermes.argawaen.net`).
"""

import logging

from .state import build_state

logger = logging.getLogger("apps.fleet")


def _index(state):
    """Les lignes de `build_state()`, indexées par adresse et par nom."""
    by_ip, by_name = {}, {}
    for row in state["machines"]:
        if row.get("ip"):
            by_ip[row["ip"]] = row
        by_name[row["name"].lower()] = row
    return by_ip, by_name


def _match(row_by_ip, row_by_name, *candidates):
    """La première correspondance parmi les adresses puis les noms proposés."""
    for value in candidates:
        if not value:
            continue
        hit = row_by_ip.get(value)
        if hit:
            return hit
    for value in candidates:
        if not value:
            continue
        name = str(value).lower()
        hit = row_by_name.get(name) or row_by_name.get(name.split(".", 1)[0])
        if hit:
            return hit
    return None


def annotate(categories):
    """Accroche `.flotte` à chaque machine et serveur des catégories fournies.

    `.flotte` est la ligne de `build_state()` (facts, drift, images, stacks, observed)
    ou `None` quand la machine n'est pas dans l'inventaire du lab — un service hébergé
    ailleurs, par exemple, qui reste parfaitement légitime sur la page.

    Modifie les objets en place et ne les enregistre pas : c'est de l'affichage.
    """
    try:
        state = build_state(sync=False)
    except Exception:
        # Une page de monitoring qui tombe parce que wud ou la base de la flotte a
        # hoqueté serait le comble : on affiche la structure sans l'enrichissement.
        logger.warning("enrichissement flotte indisponible", exc_info=True)
        return categories

    by_ip, by_name = _index(state)

    for categorie in categories:
        for machine in categorie.machines.all():
            machine.flotte = _match(
                by_ip, by_name,
                getattr(machine, "ip_statique", None),
                getattr(machine, "adresse_ip", None),
                machine.nom,
            )
        for serveur in categorie.serveurs.all():
            serveur.flotte = _match(
                by_ip, by_name,
                getattr(serveur, "adresse", None),
                getattr(serveur, "hostname", None),
                serveur.titre,
            )
    return categories
