"""Quelles cibles cette app supervise, et lesquelles elle laisse à gatus.

Le lab fait tourner deux moteurs de disponibilité : gatus possède les machines et
les services déclarés (ses endpoints sont en YAML dans git et c'est lui qui alerte),
cette app possède tout le reste de ce que le scanner trouve sur le LAN — téléphones,
IoT, caméras, imprimantes. Une machine déclarée dans `_common/inventory.conf` n'a
donc aucun check ici, et la jointure se fait sur `fleet.Machine`, qui reflète ce
fichier, plutôt que sur une liste répétée dans ce dépôt.
"""

import logging

logger = logging.getLogger("apps")


def owned_by_gatus(ip_address):
    """Cette adresse est-elle une machine déclarée, donc déjà surveillée par gatus ?"""
    # Importé ici : évite un cycle entre `apps.monitoring` et `apps.fleet`.
    from apps.fleet.models import Machine

    if not ip_address:
        return False
    return Machine.objects.filter(ip=ip_address, retired=False).exists()


def ensure_default_check(device):
    """Donne son check ICMP par défaut à un appareil, sauf si gatus le possède.

     :param device : L'appareil découvert.
     :return : Le check, ou None quand l'appareil est une machine déclarée.
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
