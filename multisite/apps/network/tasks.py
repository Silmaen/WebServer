"""Tâches de scan réseau : interrogation de la gateway, scan rapide, scan complet.

Les trois scans ne diffèrent que par leur source d'hôtes : la suite — création ou
mise à jour des appareils, marquage des disparus, résumé — est commune et vit dans
les helpers privés du module.
"""

import logging
from ipaddress import IPv4Address, IPv4Network

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("apps")


@shared_task
def schedule_due_scans():
    """Programme les scans par gateway dont l'intervalle est écoulé.

    Seuls les réseaux dotés d'identifiants de gateway sont scannés
    automatiquement ; les autres se scannent à la main.
    """
    from apps.core.models import BackgroundTask
    from apps.core.tasks import dispatch_task
    from apps.network.models import Network

    now = timezone.now()
    dispatched = 0
    for network in Network.objects.filter(is_active=True).select_related("gateway_credential"):
        if not network.can_query_gateway:
            continue
        ecoule = (now - network.last_scan).total_seconds() if network.last_scan else None
        if ecoule is not None and ecoule < network.scan_interval:
            continue

        # Ne pas empiler un second scan du même réseau.
        already_running = BackgroundTask.objects.filter(
            name__contains=network.name,
            status__in=[BackgroundTask.Status.PENDING, BackgroundTask.Status.RUNNING],
        ).exists()
        if already_running:
            continue

        dispatch_task(
            gateway_scan_task,
            args=[str(network.pk)],
            name=f"Gateway scan : {network.name}",
        )
        dispatched += 1

    if dispatched:
        logger.info("%d scans de gateway programmés", dispatched)


def _charger_reseau(tlog, network_id, avec_credential=False):
    """Le réseau visé, ou None après avoir marqué la tâche en échec."""
    from apps.network.models import Network

    qs = Network.objects
    if avec_credential:
        qs = qs.select_related("gateway_credential")
    try:
        return qs.get(pk=network_id)
    except Network.DoesNotExist:
        tlog.failure(f"Réseau {network_id} introuvable")
        return None


def _enregistrer_hote(tlog, network, hote, now, complet=False):
    """Crée ou met à jour l'appareil correspondant à un hôte découvert.

     :param hote : Un objet portant ip, mac, hostname, manufacturer (et, en mode
        complet, open_ports, guessed_category, extra_data).
     :param complet : Vrai pour un scan complet, qui reporte aussi ports et catégorie.
     :return : "created" ou "updated".
    """
    from apps.devices.models import ConnectionLog, Device
    from apps.monitoring.policy import ensure_default_check

    defaults = {
        "hostname": hote.hostname,
        "mac_address": hote.mac,
        "manufacturer": hote.manufacturer,
        "category": hote.guessed_category if complet else "unknown",
        "status": Device.Status.ONLINE,
        "network": network,
        "last_seen": now,
    }
    if complet:
        defaults["open_ports"] = list(hote.open_ports)
        defaults["extra_data"] = hote.extra_data

    device, created = Device.objects.get_or_create(ip_address=hote.ip, defaults=defaults)

    # Une machine déclarée est l'affaire de gatus, pas la nôtre -- voir
    # apps/monitoring/policy.py pour le partage des cibles entre les deux moteurs.
    ensure_default_check(device)

    if created:
        _journaliser(device, ConnectionLog.Event.CONNECTED, network, hote.mac)
        tlog.info(
            "+ Nouveau : %s (%s) - %s",
            hote.hostname, hote.ip, hote.manufacturer or "fabricant inconnu",
        )
        return "created"

    was_offline = device.status == Device.Status.OFFLINE
    if complet:
        _fusionner_complet(device, hote, network, now, tlog)
    else:
        _fusionner_presence(device, hote, now)

    if was_offline:
        _journaliser(
            device, ConnectionLog.Event.CONNECTED, network, hote.mac or device.mac_address,
        )
        tlog.info("↑ Reconnecté : %s (%s)", device.hostname, hote.ip)
    elif complet:
        tlog.info(
            "  Mis à jour : %s (%s) - %d ports",
            device.hostname, hote.ip, len(hote.open_ports),
        )
    return "updated"


def _fusionner_presence(device, hote, now):
    """Complète l'appareil avec ce qu'un scan de présence apprend, sans écraser."""
    from apps.devices.models import Device

    if hote.mac and not device.mac_address:
        device.mac_address = hote.mac
    if hote.manufacturer and not device.manufacturer:
        device.manufacturer = hote.manufacturer
    if hote.hostname and hote.hostname != hote.ip and device.hostname == device.ip_address:
        device.hostname = hote.hostname
    device.last_seen = now
    if device.status == Device.Status.OFFLINE:
        device.status = Device.Status.ONLINE
    device.save(
        update_fields=["mac_address", "manufacturer", "hostname", "last_seen", "status"],
    )


def _fusionner_complet(device, hote, network, now, tlog):
    """Reporte tout ce qu'un scan complet apprend : ports, OS, catégorie."""
    from apps.devices.models import Device

    device.mac_address = hote.mac or device.mac_address
    device.manufacturer = hote.manufacturer or device.manufacturer
    device.open_ports = list(hote.open_ports) if hote.open_ports else device.open_ports
    device.last_seen = now
    device.network = network

    if hote.hostname and hote.hostname != hote.ip:
        device.hostname = hote.hostname
    if hote.extra_data:
        device.extra_data = {**device.extra_data, **hote.extra_data}
    if hote.guessed_category != "unknown" and device.category == "unknown":
        tlog.info(
            "  Reclassé %s : %s → %s",
            device.hostname, device.category, hote.guessed_category,
        )
        device.category = hote.guessed_category
    if device.status == Device.Status.OFFLINE:
        device.status = Device.Status.ONLINE
    device.save()


def _journaliser(device, event, network, mac=""):
    """Ajoute une entrée au journal de connexion de l'appareil."""
    from apps.devices.models import ConnectionLog

    ConnectionLog.objects.create(
        device=device, event=event,
        ip_address=device.ip_address, mac_address=mac or device.mac_address,
        network=network,
    )


def _marquer_disparus(tlog, network, discovered_ips):
    """Passe hors ligne les appareils du réseau que le scan n'a pas revus."""
    from apps.devices.models import ConnectionLog, Device

    absents = (
        network.devices.filter(status=Device.Status.ONLINE)
        .exclude(ip_address__in=discovered_ips)
    )
    for device in absents:
        device.status = Device.Status.OFFLINE
        device.save(update_fields=["status"])
        _journaliser(device, ConnectionLog.Event.DISCONNECTED, network)
        tlog.info("↓ Déconnecté : %s (%s)", device.hostname, device.ip_address)


def _traiter_hotes(tlog, network, hotes, scan_type, complet=False):
    """Enregistre les hôtes, marque les disparus, horodate le réseau, rend le résumé."""
    now = timezone.now()
    compteurs = {"created": 0, "updated": 0}
    discovered_ips = set()

    for hote in hotes:
        discovered_ips.add(hote.ip)
        compteurs[_enregistrer_hote(tlog, network, hote, now, complet=complet)] += 1

    _marquer_disparus(tlog, network, discovered_ips)

    network.last_scan = now
    network.save(update_fields=["last_scan"])

    result = {
        "network": network.name,
        "cidr": network.cidr,
        "hosts_found": len(hotes),
        "created": compteurs["created"],
        "updated": compteurs["updated"],
        "scan_type": scan_type,
    }
    tlog.info(
        "Résumé : %d trouvés, %d nouveaux, %d mis à jour",
        len(hotes), compteurs["created"], compteurs["updated"],
    )
    tlog.success(result)
    return result


@shared_task(bind=True, max_retries=0, queue="network")
def gateway_scan_task(self, network_id: str):
    """Interroge la gateway OpenWrt pour ses appareils connectés."""
    from apps.core.tasks import TaskLogger
    from apps.network.discovery import lookup_mac_vendor, resolve_hostname
    from apps.network.gateway import query_gateway

    tlog = TaskLogger(self)
    tlog.start()

    network = _charger_reseau(tlog, network_id, avec_credential=True)
    if network is None:
        return {"error": "Réseau introuvable"}
    if not network.can_query_gateway:
        tlog.failure(f"Pas de gateway/credential pour {network.name}")
        return {"error": "Identifiants de gateway absents"}

    tlog.info(
        "Interrogation de la gateway %s pour %s (%s)",
        network.gateway, network.name, network.cidr,
    )
    try:
        gw_hosts = query_gateway(network.gateway, network.gateway_credential)
    except Exception as e:
        tlog.failure(f"Erreur gateway : {e}")
        return {"error": str(e)}

    try:
        cidr = IPv4Network(network.cidr, strict=False)
    except ValueError:
        tlog.failure(f"CIDR invalide : {network.cidr}")
        return {"error": f"CIDR invalide : {network.cidr}"}

    # La gateway voit aussi les autres réseaux qu'elle route : ne garder que le nôtre.
    all_count = len(gw_hosts)
    gw_hosts = [h for h in gw_hosts if IPv4Address(h.ip) in cidr]
    tlog.info("%d hôtes via gateway, %d dans le CIDR %s", all_count, len(gw_hosts), network.cidr)

    # La gateway ne résout pas les noms hors DHCP, ni les fabricants : on complète.
    for gw_host in gw_hosts:
        gw_host.hostname = gw_host.hostname or resolve_hostname(gw_host.ip) or gw_host.ip
        gw_host.manufacturer = lookup_mac_vendor(gw_host.mac) if gw_host.mac else ""

    return _traiter_hotes(tlog, network, gw_hosts, "gateway")


@shared_task(bind=True, max_retries=0, queue="network")
def quick_scan_task(self, network_id: str):
    """Scan de présence : ARP + ping. Repli quand il n'y a pas d'accès gateway."""
    from apps.core.tasks import TaskLogger
    from apps.network.discovery import quick_scan

    tlog = TaskLogger(self)
    tlog.start()

    network = _charger_reseau(tlog, network_id)
    if network is None:
        return {"error": "Réseau introuvable"}

    tlog.info("Scan rapide du réseau %s (%s)", network.name, network.cidr)
    hosts = quick_scan(network.cidr)
    tlog.info("%d hôtes détectés par ARP/ping", len(hosts))

    return _traiter_hotes(tlog, network, hosts, "quick")


@shared_task(bind=True, max_retries=0, queue="network")
def discover_network_task(self, network_id: str):
    """Scan complet : ARP + ping + ports + OS. Lent, réservé au scan manuel."""
    from apps.core.tasks import TaskLogger
    from apps.network.discovery import full_scan

    tlog = TaskLogger(self)
    tlog.start()

    network = _charger_reseau(tlog, network_id)
    if network is None:
        return {"error": "Réseau introuvable"}

    tlog.info("Scan complet du réseau %s (%s)", network.name, network.cidr)
    hosts = full_scan(network.cidr)
    tlog.info("%d hôtes détectés (ARP + ping + scan de ports)", len(hosts))

    return _traiter_hotes(tlog, network, hosts, "full", complet=True)
