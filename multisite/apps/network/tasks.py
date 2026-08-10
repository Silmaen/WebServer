import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("apps")


@shared_task
def schedule_due_scans():
    """Find networks due for scanning via gateway query (automatic mode).

    Only networks with a configured gateway credential are scanned automatically.
    Networks without gateway credentials must be scanned manually.
    """
    from apps.core.models import BackgroundTask
    from apps.core.tasks import dispatch_task
    from apps.network.models import Network

    now = timezone.now()
    dispatched = 0
    for network in Network.objects.filter(is_active=True).select_related("gateway_credential"):
        if not network.can_query_gateway:
            continue

        if network.last_scan is not None and (now - network.last_scan).total_seconds() < network.scan_interval:
            continue

        # Check no scan is already running for this network
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
        logger.info("Dispatched %d gateway scans", dispatched)


@shared_task(bind=True, max_retries=0, queue="network")
def gateway_scan_task(self, network_id: str):
    """Query the OpenWrt gateway for connected devices, then probe new ones."""
    from apps.core.tasks import TaskLogger
    from apps.devices.models import ConnectionLog, Device
    from apps.monitoring.policy import ensure_default_check
    from apps.network.discovery import lookup_mac_vendor, resolve_hostname
    from apps.network.gateway import query_gateway
    from apps.network.models import Network

    tlog = TaskLogger(self)
    tlog.start()

    try:
        network = Network.objects.select_related("gateway_credential").get(pk=network_id)
    except Network.DoesNotExist:
        tlog.failure(f"Réseau {network_id} introuvable")
        return {"error": "Network not found"}

    if not network.can_query_gateway:
        tlog.failure(f"Pas de gateway/credential pour {network.name}")
        return {"error": "No gateway credentials"}

    tlog.info("Interrogation de la gateway %s pour %s (%s)", network.gateway, network.name, network.cidr)

    try:
        gw_hosts = query_gateway(network.gateway, network.gateway_credential)
    except Exception as e:
        tlog.failure(f"Erreur gateway : {e}")
        return {"error": str(e)}

    # Filter: only keep hosts whose IP belongs to this network's CIDR
    from ipaddress import IPv4Address, IPv4Network
    try:
        cidr = IPv4Network(network.cidr, strict=False)
    except ValueError:
        tlog.failure(f"CIDR invalide : {network.cidr}")
        return {"error": f"Invalid CIDR: {network.cidr}"}

    all_count = len(gw_hosts)
    gw_hosts = [h for h in gw_hosts if IPv4Address(h.ip) in cidr]
    tlog.info("%d hôtes via gateway, %d dans le CIDR %s", all_count, len(gw_hosts), network.cidr)

    now = timezone.now()

    created_count = 0
    updated_count = 0
    discovered_ips = set()

    for gw_host in gw_hosts:
        discovered_ips.add(gw_host.ip)

        # Enrich: resolve hostname if not from DHCP, lookup MAC vendor
        hostname = gw_host.hostname or resolve_hostname(gw_host.ip) or gw_host.ip
        manufacturer = lookup_mac_vendor(gw_host.mac) if gw_host.mac else ""

        device, created = Device.objects.get_or_create(
            ip_address=gw_host.ip,
            defaults={
                "hostname": hostname,
                "mac_address": gw_host.mac,
                "manufacturer": manufacturer,
                "category": "unknown",
                "status": Device.Status.ONLINE,
                "network": network,
                "last_seen": now,
            },
        )

        # A declared machine is gatus's business, not this app's -- see
        # apps/monitoring/policy.py for why the two engines split by target.
        ensure_default_check(device)

        if created:
            created_count += 1
            ConnectionLog.objects.create(
                device=device, event=ConnectionLog.Event.CONNECTED,
                ip_address=gw_host.ip, mac_address=gw_host.mac, network=network,
            )
            tlog.info("+ Nouveau : %s (%s) - %s [%s]",
                      hostname, gw_host.ip, manufacturer or "?", gw_host.source)
        else:
            updated_count += 1
            was_offline = device.status == Device.Status.OFFLINE

            if gw_host.mac and not device.mac_address:
                device.mac_address = gw_host.mac
            if manufacturer and not device.manufacturer:
                device.manufacturer = manufacturer
            if hostname and hostname != gw_host.ip and device.hostname == device.ip_address:
                device.hostname = hostname

            device.last_seen = now
            if device.status == Device.Status.OFFLINE:
                device.status = Device.Status.ONLINE
            device.save(update_fields=["mac_address", "manufacturer", "hostname", "last_seen", "status"])

            if was_offline:
                ConnectionLog.objects.create(
                    device=device, event=ConnectionLog.Event.CONNECTED,
                    ip_address=gw_host.ip, mac_address=gw_host.mac or device.mac_address,
                    network=network,
                )
                tlog.info("↑ Reconnecté : %s (%s)", device.hostname, gw_host.ip)

    # Mark devices not found as disconnected
    online_devices = network.devices.filter(status=Device.Status.ONLINE).exclude(ip_address__in=discovered_ips)
    for device in online_devices:
        device.status = Device.Status.OFFLINE
        device.save(update_fields=["status"])
        ConnectionLog.objects.create(
            device=device, event=ConnectionLog.Event.DISCONNECTED,
            ip_address=device.ip_address, mac_address=device.mac_address,
            network=network,
        )
        tlog.info("↓ Déconnecté : %s (%s)", device.hostname, device.ip_address)

    network.last_scan = now
    network.save(update_fields=["last_scan"])

    result = {
        "network": network.name,
        "cidr": network.cidr,
        "hosts_found": len(gw_hosts),
        "created": created_count,
        "updated": updated_count,
        "scan_type": "gateway",
    }
    tlog.info("Résumé : %d trouvés, %d nouveaux, %d mis à jour", len(gw_hosts), created_count, updated_count)
    tlog.success(result)
    return result


@shared_task(bind=True, max_retries=0, queue="network")
def quick_scan_task(self, network_id: str):
    """Quick presence scan: ARP + ping only. Fallback when no gateway credentials."""
    from apps.core.tasks import TaskLogger
    from apps.devices.models import ConnectionLog, Device
    from apps.monitoring.policy import ensure_default_check
    from apps.network.discovery import quick_scan
    from apps.network.models import Network

    tlog = TaskLogger(self)
    tlog.start()

    try:
        network = Network.objects.get(pk=network_id)
    except Network.DoesNotExist:
        tlog.failure(f"Réseau {network_id} introuvable")
        return {"error": "Network not found"}

    tlog.info("Scan rapide du réseau %s (%s)", network.name, network.cidr)

    hosts = quick_scan(network.cidr)
    now = timezone.now()

    tlog.info("%d hôtes détectés par ARP/ping", len(hosts))

    created_count = 0
    updated_count = 0
    discovered_ips = set()

    for host in hosts:
        discovered_ips.add(host.ip)
        device, created = Device.objects.get_or_create(
            ip_address=host.ip,
            defaults={
                "hostname": host.hostname,
                "mac_address": host.mac,
                "manufacturer": host.manufacturer,
                "category": "unknown",
                "status": Device.Status.ONLINE,
                "network": network,
                "last_seen": now,
            },
        )

        # A declared machine is gatus's business, not this app's -- see
        # apps/monitoring/policy.py for why the two engines split by target.
        ensure_default_check(device)

        if created:
            created_count += 1
            ConnectionLog.objects.create(
                device=device, event=ConnectionLog.Event.CONNECTED,
                ip_address=host.ip, mac_address=host.mac, network=network,
            )
            tlog.info("+ Nouveau : %s (%s) - %s", host.hostname, host.ip, host.manufacturer or "fabricant inconnu")
        else:
            updated_count += 1
            was_offline = device.status == Device.Status.OFFLINE

            if host.mac and not device.mac_address:
                device.mac_address = host.mac
            if host.manufacturer and not device.manufacturer:
                device.manufacturer = host.manufacturer
            if host.hostname and host.hostname != host.ip and device.hostname == device.ip_address:
                device.hostname = host.hostname

            device.last_seen = now
            if device.status == Device.Status.OFFLINE:
                device.status = Device.Status.ONLINE
            device.save(update_fields=["mac_address", "manufacturer", "hostname", "last_seen", "status"])

            if was_offline:
                ConnectionLog.objects.create(
                    device=device, event=ConnectionLog.Event.CONNECTED,
                    ip_address=host.ip, mac_address=host.mac or device.mac_address,
                    network=network,
                )
                tlog.info("↑ Reconnecté : %s (%s)", device.hostname, host.ip)

    # Mark devices not found as disconnected
    online_devices = network.devices.filter(status=Device.Status.ONLINE).exclude(ip_address__in=discovered_ips)
    for device in online_devices:
        device.status = Device.Status.OFFLINE
        device.save(update_fields=["status"])
        ConnectionLog.objects.create(
            device=device, event=ConnectionLog.Event.DISCONNECTED,
            ip_address=device.ip_address, mac_address=device.mac_address,
            network=network,
        )
        tlog.info("↓ Déconnecté : %s (%s)", device.hostname, device.ip_address)

    network.last_scan = now
    network.save(update_fields=["last_scan"])

    result = {
        "network": network.name,
        "cidr": network.cidr,
        "hosts_found": len(hosts),
        "created": created_count,
        "updated": updated_count,
        "scan_type": "quick",
    }
    tlog.info("Résumé : %d trouvés, %d nouveaux, %d mis à jour", len(hosts), created_count, updated_count)
    tlog.success(result)
    return result


@shared_task(bind=True, max_retries=0, queue="network")
def discover_network_task(self, network_id: str):
    """Full discovery: ARP + ping + ports + OS. Slow, used for manual deep scan."""
    from apps.core.tasks import TaskLogger
    from apps.devices.models import ConnectionLog, Device
    from apps.monitoring.policy import ensure_default_check
    from apps.network.discovery import full_scan
    from apps.network.models import Network

    tlog = TaskLogger(self)
    tlog.start()

    try:
        network = Network.objects.get(pk=network_id)
    except Network.DoesNotExist:
        tlog.failure(f"Réseau {network_id} introuvable")
        return {"error": "Network not found"}

    tlog.info("Scan complet du réseau %s (%s)", network.name, network.cidr)
    tlog.info("Phase 1: Détection ARP + ping...")

    hosts = full_scan(network.cidr)
    now = timezone.now()

    tlog.info("%d hôtes détectés (ARP + ping + scan de ports)", len(hosts))

    created_count = 0
    updated_count = 0
    discovered_ips = set()

    for host in hosts:
        discovered_ips.add(host.ip)
        device, created = Device.objects.get_or_create(
            ip_address=host.ip,
            defaults={
                "hostname": host.hostname,
                "mac_address": host.mac,
                "manufacturer": host.manufacturer,
                "category": host.guessed_category,
                "status": Device.Status.ONLINE,
                "network": network,
                "open_ports": [p for p in host.open_ports],
                "last_seen": now,
                "extra_data": host.extra_data,
            },
        )

        # A declared machine is gatus's business, not this app's -- see
        # apps/monitoring/policy.py for why the two engines split by target.
        ensure_default_check(device)

        if created:
            created_count += 1
            ConnectionLog.objects.create(
                device=device, event=ConnectionLog.Event.CONNECTED,
                ip_address=host.ip, mac_address=host.mac, network=network,
            )
            ports_str = ", ".join(str(p["port"]) for p in host.open_ports[:5]) if host.open_ports else "aucun"
            tlog.info("+ Nouveau : %s (%s) - %s - catégorie: %s - ports: %s",
                      host.hostname, host.ip, host.manufacturer or "?", host.guessed_category, ports_str)
        else:
            updated_count += 1
            was_offline = device.status == Device.Status.OFFLINE
            device.mac_address = host.mac or device.mac_address
            device.manufacturer = host.manufacturer or device.manufacturer
            device.open_ports = [p for p in host.open_ports] if host.open_ports else device.open_ports
            device.last_seen = now
            device.network = network

            if host.hostname and host.hostname != host.ip:
                device.hostname = host.hostname
            if host.extra_data:
                device.extra_data = {**device.extra_data, **host.extra_data}
            if host.guessed_category != "unknown" and device.category == "unknown":
                old_cat = device.category
                device.category = host.guessed_category
                tlog.info("  Reclassé %s : %s → %s", device.hostname, old_cat, host.guessed_category)
            if device.status == Device.Status.OFFLINE:
                device.status = Device.Status.ONLINE

            device.save()

            if was_offline:
                ConnectionLog.objects.create(
                    device=device, event=ConnectionLog.Event.CONNECTED,
                    ip_address=host.ip, mac_address=host.mac or device.mac_address,
                    network=network,
                )
                tlog.info("↑ Reconnecté : %s (%s)", device.hostname, host.ip)
            else:
                tlog.info("  Mis à jour : %s (%s) - %d ports", device.hostname, host.ip, len(host.open_ports))

    # Mark devices not found as disconnected
    online_devices = network.devices.filter(status=Device.Status.ONLINE).exclude(ip_address__in=discovered_ips)
    for device in online_devices:
        device.status = Device.Status.OFFLINE
        device.save(update_fields=["status"])
        ConnectionLog.objects.create(
            device=device, event=ConnectionLog.Event.DISCONNECTED,
            ip_address=device.ip_address, mac_address=device.mac_address,
            network=network,
        )
        tlog.info("↓ Déconnecté : %s (%s)", device.hostname, device.ip_address)

    network.last_scan = now
    network.save(update_fields=["last_scan"])

    result = {
        "network": network.name,
        "cidr": network.cidr,
        "hosts_found": len(hosts),
        "created": created_count,
        "updated": updated_count,
        "scan_type": "full",
    }
    tlog.info("Résumé : %d trouvés, %d nouveaux, %d mis à jour", len(hosts), created_count, updated_count)
    tlog.success(result)
    return result
