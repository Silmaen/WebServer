"""Sondes par appareil : scan de ports, détection d'OS, reclassement."""

import logging
from datetime import datetime

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("apps")

# Délai avant de resonder un appareil, en secondes (24 h).
PROBE_INTERVAL = 86400


def _run_probe(self, device_id: str, mode: str = "quick"):
    """Corps commun aux sondes rapide et approfondie.

     :param self : La tâche Celery liée, pour son journal.
     :param mode : "quick" ou "deep".
     :return : Un résumé du scan, ou None si l'appareil a disparu.
    """
    # Importés dans la tâche : les modèles ne sont pas chargés à l'import du module
    # par le worker Celery.
    from apps.core.tasks import TaskLogger
    from apps.devices.models import Device
    from apps.network.discovery import guess_category, scan_ports

    tlog = TaskLogger(self)
    tlog.start()

    try:
        device = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        tlog.failure(f"Appareil {device_id} introuvable")
        return None

    label = "Quick probe" if mode == "quick" else "Deep probe"
    tlog.info("%s de %s (%s)", label, device.hostname, device.ip_address)

    try:
        ports, os_info = scan_ports(device.ip_address, mode=mode)
    except Exception as e:
        tlog.failure(f"Erreur nmap : {e}")
        return {"error": str(e)}

    tlog.info("%d ports ouverts trouvés", len(ports))

    device.open_ports = ports
    update_fields = ["open_ports", "extra_data"]

    if os_info:
        device.extra_data = {**device.extra_data, "os_detection": os_info}
        os_names = [m["name"] for m in os_info.get("os_matches", [])[:2]]
        tlog.info("OS détecté : %s", ", ".join(os_names) if os_names else "inconnu")

    # Deviner la catégorie depuis les ports et l'OS, si elle est encore inconnue.
    if device.category == "unknown" and (ports or os_info):
        new_cat = guess_category(ports, os_info)
        if new_cat != "unknown":
            tlog.info("Catégorie déduite : %s → %s", device.category, new_cat)
            device.category = new_cat
            update_fields.append("category")

    device.extra_data["last_probe_at"] = timezone.now().isoformat()
    device.extra_data["last_probe_mode"] = mode
    device.save(update_fields=update_fields)

    ports_summary = (
        ", ".join(f"{p['port']}/{p['protocol']}" for p in ports[:10]) if ports else "aucun"
    )
    tlog.info("Ports : %s", ports_summary)
    tlog.success({
        "device": device.hostname,
        "ports": len(ports),
        "mode": mode,
        "os": _premier_os(os_info),
    })
    return {"device": device.hostname, "ports_found": len(ports)}


def _premier_os(os_info):
    """Le nom du meilleur OS deviné, ou "?" quand nmap n'a rien conclu."""
    matches = os_info.get("os_matches") or []
    return matches[0].get("name", "?") if matches else "?"


@shared_task(bind=True, max_retries=0, queue="network")
def quick_probe_task(self, device_id: str):
    """Sonde rapide : 100 ports les plus courants + détection d'OS (~30 s)."""
    return _run_probe(self, device_id, mode="quick")


@shared_task(bind=True, max_retries=0, queue="network")
def deep_probe_task(self, device_id: str):
    """Sonde approfondie : tous les ports TCP + top 1000 UDP + versions (~5-15 min)."""
    return _run_probe(self, device_id, mode="deep")


@shared_task(queue="network")
def schedule_device_probes():
    """Programme une sonde rapide pour les appareils en ligne sondés il y a longtemps."""
    from apps.core.tasks import dispatch_task
    from apps.devices.models import Device

    cutoff = timezone.now() - timezone.timedelta(seconds=PROBE_INTERVAL)
    dispatched = 0

    for device in Device.objects.filter(status=Device.Status.ONLINE):
        if _sonde_recente(device, cutoff):
            continue
        dispatch_task(
            quick_probe_task,
            args=[str(device.pk)],
            name=f"Quick probe : {device.hostname}",
        )
        dispatched += 1

    if dispatched:
        logger.info("%d sondes d'appareils programmées", dispatched)


def _sonde_recente(device, cutoff):
    """L'appareil a-t-il été sondé après `cutoff` ?"""
    last_probe = device.extra_data.get("last_probe_at")
    if not last_probe:
        return False
    try:
        return datetime.fromisoformat(last_probe) > cutoff
    except (ValueError, TypeError):
        return False
