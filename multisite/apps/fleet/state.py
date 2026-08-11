"""Assemble la vue de la flotte depuis ses quatre sources indépendantes.

Chaque source est interrogée sur ce dont elle est l'autorité, et aucune n'est
réimplémentée ici : `Report` dit qui rapporte encore et ce qui a dérivé, `Stack` ce
qui est déployé, wud quelles images ont un tag plus récent, et
`_common/inventory.conf` quelles machines sont censées exister. Cette dernière est
la raison pour laquelle une machine qui n'a **jamais** rapporté apparaît quand même :
c'est le cas intéressant, et une page bâtie sur les seuls rapports ne peut pas le
montrer.
"""

from django.utils import timezone

from apps.devices.models import Device

from . import inventory, wud
from .models import Machine, Report, Stack


def _latest_reports(machines):
    """Un rapport par machine, le plus récent — en deux requêtes plutôt que N."""
    latest = {}
    reports = (
        Report.objects.filter(machine__in=machines)
        .order_by("machine_id", "-at")
        .distinct("machine_id")
    )
    for report in reports:
        latest[report.machine_id] = report
    return latest


def _stacks_by_machine(machines):
    """Les stacks déployées, groupées par machine."""
    grouped = {}
    for stack in Stack.objects.filter(machine__in=machines).select_related("machine"):
        grouped.setdefault(stack.machine_id, []).append(stack)
    return grouped


def build_state(sync=True):
    """La flotte entière, en données brutes. Utilisé par la page et par l'API.

     :param sync : Faux pour sauter la relecture de l'inventaire.
     :return : Un dict avec la date, l'erreur wud éventuelle et les lignes machines.
    """
    if sync:
        inventory.sync()

    machines = list(Machine.objects.filter(retired=False))
    reports = _latest_reports(machines)
    stacks = _stacks_by_machine(machines)
    containers, wud_error = wud.containers()
    images = wud.by_machine(containers)
    par_conteneur = wud.by_container(containers)

    # Le côté observé, joint sur l'adresse : rapprocher un Device d'une machine
    # déclarée est tout l'intérêt de garder les deux tables séparées.
    observed = {d.ip_address: d for d in Device.objects.exclude(ip_address=None)}

    rows = [
        _ligne(machine, reports, stacks, images, observed, par_conteneur)
        for machine in machines
    ]

    return {
        "generated": timezone.now(),
        "wud_error": wud_error,
        "machines": rows,
        # Le côté découverte en compteur et non en liste : sur un LAN domestique la
        # plupart des appareils observés sont *censés* être non déclarés.
        "observed_total": len(observed),
        "observed_declared": sum(1 for r in rows if r["observed"]),
    }


def _attacher_images(stacks, containers):
    """Pose sur chaque stack les conteneurs wud qui lui appartiennent.

    Appariement sur le label compose quand wud l'expose, sinon sur le préfixe du nom
    de conteneur — projets les plus longs d'abord, parce qu'un nom de service peut
    contenir des tirets et que deux projets peuvent partager un préfixe.
    """
    par_projet = {stack.project: [] for stack in stacks}
    projets = sorted(par_projet, key=len, reverse=True)

    for container in containers:
        projet = container["project"] if container["project"] in par_projet else ""
        if not projet:
            projet = next(
                (p for p in projets if container["container"].startswith((f"{p}-", f"{p}_"))),
                "",
            )
        if projet:
            par_projet[projet].append(container)

    for stack in stacks:
        siens = par_projet[stack.project]
        # Attribut posé en mémoire, comme `enrich.annotate` : c'est de l'affichage.
        stack.images = {
            "total": len(siens),
            "behind": [c for c in siens if c["update"]],
        }


def _ligne(machine, reports, stacks, images, observed, par_conteneur):
    """Une machine déclarée, augmentée de ce que les quatre sources en savent."""
    report = reports.get(machine.id)
    device = observed.get(machine.ip) if machine.ip else None
    disk_percent, disk_mount = report.worst_disk if report else (0, "")
    machine_stacks = stacks.get(machine.id, [])
    _attacher_images(machine_stacks, par_conteneur.get(machine.name, []))

    return {
        "name": machine.name,
        "ip": machine.ip,
        "role": machine.role,
        "os_family": machine.os_family,
        "wake_order": machine.wake_order,
        # `never reported` plutôt qu'un blanc : « aucune idée » et « rien à signaler »
        # sont deux réponses différentes, et les confondre fait passer un agent cassé
        # pour une machine en bonne santé pendant des semaines.
        "state": report.state if report else "never reported",
        "age": report.age_seconds if report else None,
        "at": report.at if report else None,
        "facts": report.facts if report else {},
        "drift": {
            "status": report.drift_status if report else "unknown",
            "count": report.drift_count if report else 0,
            "changes": report.drift_changes if report else [],
        },
        "disk": {"percent": disk_percent, "mount": disk_mount},
        "images": images.get(machine.name, {"total": 0, "behind": []}),
        "stacks": machine_stacks,
        "stack_alerts": [s for s in machine_stacks if s.severity == "danger"],
        "observed": (
            {"status": device.status, "last_seen": device.last_seen, "hostname": device.hostname}
            if device
            else None
        ),
    }


def _stack_json(stack):
    """Une `Stack` en données brutes, propriétés calculées comprises."""
    return {
        "project": stack.project,
        "path": stack.path,
        "remote": stack.remote,
        "repo": stack.repo,
        "foreign": stack.foreign,
        "head": stack.head,
        "worktree": stack.worktree,
        "behind": stack.behind,
        "compose": stack.compose,
        "deploy_script": stack.deploy_script,
        "deployable": stack.deployable,
        "severity": stack.severity,
        # Posé par `_attacher_images`, absent si l'état n'est pas passé par là.
        "images": getattr(stack, "images", None),
        "first_seen": stack.first_seen,
        "last_seen": stack.last_seen,
    }


def as_json(state):
    """`build_state()` pour un consommateur JSON.

    La page a besoin des instances de modèles (elle appelle leurs propriétés), qui ne
    sont pas sérialisables : la conversion vit donc ici, et les règles de gravité
    restent sur le modèle au lieu d'être dupliquées par chaque consommateur.
    """
    return {
        **state,
        "machines": [
            {
                **row,
                "stacks": [_stack_json(s) for s in row["stacks"]],
                "stack_alerts": [_stack_json(s) for s in row["stack_alerts"]],
            }
            for row in state["machines"]
        ],
    }
