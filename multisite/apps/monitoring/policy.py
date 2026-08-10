"""Which targets this app is the authority for.

The lab runs two availability engines on purpose, and the rule that keeps that from
being a duplication is that each one owns a different set of targets:

* **gatus** (`selene/monitoring` in the home-server-stacks repository) owns the
  declared machines and the services. Its endpoints are YAML in git, reviewed in a
  commit, and it is what alerts to the phone.
* **this app** owns everything else the scanner finds on the LAN — phones, IoT,
  cameras, printers. gatus does not watch those and should not: they come and go,
  and a dashboard full of red squares for a sleeping phone is a dashboard nobody
  reads.

So a device whose address is in `_common/inventory.conf` gets no check here. The
join is against `fleet.Machine`, which mirrors that file, rather than a list
repeated in this repository — the same reason the fleet page reads the file instead
of restating it.
"""

import logging

logger = logging.getLogger("apps")


def owned_by_gatus(ip_address):
    """Is this address a declared machine, i.e. already watched by gatus?"""
    from apps.fleet.models import Machine

    if not ip_address:
        return False
    return Machine.objects.filter(ip=ip_address, retired=False).exists()


def ensure_default_check(device):
    """Give a newly discovered device its default ICMP check, unless gatus owns it.

    Returns the check, or `None` when the device is a declared machine.
    """
    from apps.monitoring.models import MonitoringCheck

    if owned_by_gatus(device.ip_address):
        return None
    check, _ = MonitoringCheck.objects.get_or_create(
        device=device,
        check_type=MonitoringCheck.CheckType.ICMP,
        defaults={"interval": 300, "timeout": 10},
    )
    return check
