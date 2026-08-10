"""Assemble the fleet view from its four independent sources.

Each source is asked the question it is the authority on, and none of them is
reimplemented here:

| Source                  | Answers                                      |
|-------------------------|----------------------------------------------|
| `Report` (the machines) | still reporting? updates? drift? disk?       |
| `Stack` (the machines)  | what is deployed, from which checkout        |
| wud                     | which running images have a newer tag        |
| `_common/inventory.conf`| which machines are supposed to exist at all  |

The last one is why a machine that has *never* reported still appears: that is the
interesting case, and a page built only from what reported cannot show it.
"""

from django.utils import timezone

from apps.devices.models import Device

from . import inventory, wud
from .models import Machine, Report, Stack


def _latest_reports(machines):
    """One report per machine, newest first — in two queries rather than N."""
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
    grouped = {}
    for stack in Stack.objects.filter(machine__in=machines).select_related("machine"):
        grouped.setdefault(stack.machine_id, []).append(stack)
    return grouped


def build_state(sync=True):
    """The whole fleet, as plain data. Used by the page and by `/api/fleet/state/`."""
    if sync:
        inventory.sync()

    machines = list(Machine.objects.filter(retired=False))
    reports = _latest_reports(machines)
    stacks = _stacks_by_machine(machines)
    containers, wud_error = wud.containers()
    images = wud.by_machine(containers)

    # The observed side, joined on the address. A Device is what the scanner found;
    # matching it to a declared machine is the whole point of keeping the two
    # tables apart.
    observed = {d.ip_address: d for d in Device.objects.exclude(ip_address=None)}

    rows = []
    for machine in machines:
        report = reports.get(machine.id)
        device = observed.get(machine.ip) if machine.ip else None
        disk_percent, disk_mount = report.worst_disk if report else (0, "")
        machine_stacks = stacks.get(machine.id, [])

        rows.append(
            {
                "name": machine.name,
                "ip": machine.ip,
                "role": machine.role,
                "os_family": machine.os_family,
                "wake_order": machine.wake_order,
                # `never reported` rather than a blank: "I have no idea" and
                # "nothing to report" are different answers, and conflating them is
                # how a broken agent reads as a healthy machine for weeks.
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
        )

    return {
        "generated": timezone.now(),
        "wud_error": wud_error,
        "machines": rows,
        # Context for the discovery side, as a count and not a list: on a home LAN
        # most observed devices are phones and IoT and are *supposed* to be
        # undeclared. The devices page is where one browses them.
        "observed_total": len(observed),
        "observed_declared": sum(1 for r in rows if r["observed"]),
    }


def _stack_json(stack):
    """A `Stack` as plain data, including the properties the model computes."""
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
        "severity": stack.severity,
        "first_seen": stack.first_seen,
        "last_seen": stack.last_seen,
    }


def as_json(state):
    """`build_state()` for a JSON consumer.

    The page needs model instances — it calls `get_compose_display` and the
    `repo`/`foreign`/`severity` properties — and those are not serialisable. So the
    conversion lives here rather than in `build_state()`: one shape of the answer,
    one place that flattens it, and the severity rules stay on the model instead of
    being duplicated by every consumer.
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
