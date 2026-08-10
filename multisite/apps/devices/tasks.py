"""Device-level tasks: per-device port scan, OS detection, probing."""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("apps")

# How often to re-probe a device (seconds). Default: 24h.
PROBE_INTERVAL = 86400


def _run_probe(self, device_id: str, mode: str = "quick"):
    """Core probe logic shared by quick and deep tasks."""
    from apps.core.tasks import TaskLogger
    from apps.devices.models import Device
    from apps.network.discovery import guess_category, scan_ports

    tlog = TaskLogger(self)
    tlog.start()

    try:
        device = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        tlog.failure(f"Appareil {device_id} introuvable")
        return

    label = "Quick probe" if mode == "quick" else "Deep probe"
    tlog.info("%s de %s (%s)", label, device.hostname, device.ip_address)

    # Port scan + OS detection
    try:
        ports, os_info = scan_ports(device.ip_address, mode=mode)
    except Exception as e:
        tlog.failure(f"Erreur nmap : {e}")
        return {"error": str(e)}

    tlog.info("%d ports ouverts trouvés", len(ports))

    # Update device
    device.open_ports = ports
    update_fields = ["open_ports", "extra_data"]

    if os_info:
        device.extra_data = {**device.extra_data, "os_detection": os_info}
        os_names = [m["name"] for m in os_info.get("os_matches", [])[:2]]
        tlog.info("OS détecté : %s", ", ".join(os_names) if os_names else "inconnu")

    # Guess category from ports + OS if still unknown
    if device.category == "unknown" and (ports or os_info):
        new_cat = guess_category(ports, os_info)
        if new_cat != "unknown":
            tlog.info("Catégorie déduite : %s → %s", device.category, new_cat)
            device.category = new_cat
            update_fields.append("category")

    # Record probe timestamp and mode
    device.extra_data["last_probe_at"] = timezone.now().isoformat()
    device.extra_data["last_probe_mode"] = mode

    device.save(update_fields=update_fields)

    ports_summary = ", ".join(f"{p['port']}/{p['protocol']}" for p in ports[:10]) if ports else "aucun"
    tlog.info("Ports : %s", ports_summary)
    tlog.success({"device": device.hostname, "ports": len(ports), "mode": mode, "os": os_info.get("os_matches", [{}])[0].get("name", "?") if os_info.get("os_matches") else "?"})
    return {"device": device.hostname, "ports_found": len(ports)}


@shared_task(bind=True, max_retries=0, queue="network")
def quick_probe_task(self, device_id: str):
    """Quick probe: top 100 ports + OS detection (~30s)."""
    return _run_probe(self, device_id, mode="quick")


@shared_task(bind=True, max_retries=0, queue="network")
def deep_probe_task(self, device_id: str):
    """Deep probe: all 65535 TCP ports + top 1000 UDP + OS + version detection (~5-15min)."""
    return _run_probe(self, device_id, mode="deep")


@shared_task(queue="network")
def schedule_device_probes():
    """Dispatch quick probes for online devices that haven't been probed recently."""
    from apps.core.tasks import dispatch_task
    from apps.devices.models import Device

    now = timezone.now()
    cutoff = now - timezone.timedelta(seconds=PROBE_INTERVAL)

    devices = Device.objects.filter(status=Device.Status.ONLINE)
    dispatched = 0

    for device in devices:
        # Check last probe time
        last_probe = device.extra_data.get("last_probe_at")
        if last_probe:
            from datetime import datetime, timezone as tz
            try:
                last_dt = datetime.fromisoformat(last_probe)
                if last_dt > cutoff:
                    continue
            except (ValueError, TypeError):
                pass

        dispatch_task(
            quick_probe_task,
            args=[str(device.pk)],
            name=f"Quick probe : {device.hostname}",
        )
        dispatched += 1

    if dispatched:
        logger.info("Dispatched %d device probes", dispatched)
