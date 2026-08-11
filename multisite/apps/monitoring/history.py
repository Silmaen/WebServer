"""Reconstruction de l'historique des états depuis les résultats de checks.

Un `CheckResult` n'enregistre qu'un état à un instant : les transitions sont
déduites en parcourant les résultats dans l'ordre. Trois pages posent la même
question (détail d'un appareil, tableau de bord, API de supervision), d'où un seul
endroit qui y répond.
"""


def transitions(results):
    """Les changements d'état d'une suite de `(horodatage, état)` triée.

     :param results : Itérable de couples (horodatage, état), du plus ancien au plus récent.
     :return : Liste de dicts `{"time", "from", "to"}`, dans l'ordre chronologique.
    """
    changes = []
    previous = None
    for moment, status in results:
        if previous is not None and status != previous:
            changes.append({"time": moment, "from": previous, "to": status})
        previous = status
    return changes


def transitions_par_appareil(results):
    """Idem, mais pour des résultats mêlant plusieurs appareils.

     :param results : Itérable de tuples `(horodatage, état, clé d'appareil, *extra)`,
        triés par horodatage croissant.
     :return : Liste de dicts `{"time", "from", "to", "device", "extra"}`.
    """
    changes = []
    previous = {}
    for moment, status, device, *extra in results:
        before = previous.get(device)
        if before is not None and status != before:
            changes.append({
                "time": moment, "from": before, "to": status,
                "device": device, "extra": tuple(extra),
            })
        previous[device] = status
    return changes
