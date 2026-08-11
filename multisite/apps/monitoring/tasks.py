"""Tâches de supervision : programmation, exécution et purge des résultats."""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("apps")

# Nombre d'échecs consécutifs avant de déclarer un check « en panne » plutôt que
# « en erreur » : trois, pour ne pas alerter sur un paquet perdu.
ECHECS_AVANT_PANNE = 3


@shared_task
def schedule_due_checks():
    """Programme les checks dont l'intervalle est écoulé.

    Le `update(last_checked=now)` **avant** le `.delay()` est la ligne portante :
    beat appelle cette tâche toutes les 15 s alors qu'un check a un intervalle de
    300 s, donc décider depuis un `last_checked` mis à jour à l'exécution
    réempilait à chaque passage les checks déjà en file. La file grossissait sans
    jamais se vider. Le revers est qu'un check perdu attend un intervalle au lieu
    d'être rejoué aussitôt, ce qui est le bon sens du compromis.
    """
    from apps.monitoring.models import MonitoringCheck

    now = timezone.now()
    dispatched = 0
    for check in MonitoringCheck.objects.filter(is_active=True).select_related("device"):
        ecoule = (now - check.last_checked).total_seconds() if check.last_checked else None
        if ecoule is not None and ecoule < check.interval:
            continue
        MonitoringCheck.objects.filter(pk=check.pk).update(last_checked=now)
        execute_check.delay(str(check.pk))
        dispatched += 1

    if dispatched:
        logger.info("%d checks programmés", dispatched)


@shared_task
def execute_check(check_id: str):
    """Exécute un check et enregistre son résultat."""
    from apps.monitoring.checks import run_check
    from apps.monitoring.models import CheckResult, MonitoringCheck

    try:
        check = MonitoringCheck.objects.select_related("device").get(pk=check_id)
    except MonitoringCheck.DoesNotExist:
        logger.error("Check %s introuvable", check_id)
        return None

    output = run_check(
        check.check_type, check.device.ip_address, check.config, check.timeout,
    )

    check.last_checked = timezone.now()
    if output.success:
        check.current_status = MonitoringCheck.Status.UP
        check.consecutive_failures = 0
        result_status = CheckResult.Status.UP
    else:
        check.consecutive_failures += 1
        if check.consecutive_failures >= ECHECS_AVANT_PANNE:
            check.current_status = MonitoringCheck.Status.DOWN
            result_status = CheckResult.Status.DOWN
        else:
            check.current_status = MonitoringCheck.Status.FAILING
            result_status = CheckResult.Status.FAILING
    check.save(update_fields=["current_status", "last_checked", "consecutive_failures"])

    CheckResult.objects.create(
        monitoring_check=check,
        status=result_status,
        response_time_ms=output.response_time_ms,
        output=output.output,
        error=output.error,
    )

    _update_device_status(check.device)

    logger.info(
        "Check %s (%s) : %s en %.1f ms",
        check.name, check.device.ip_address, output.status, output.response_time_ms or 0,
    )
    return {
        "check_id": str(check.pk),
        "status": output.status,
        "response_time_ms": output.response_time_ms,
    }


def _update_device_status(device):
    """Déduit l'état de l'appareil de l'ensemble de ses checks actifs."""
    from apps.devices.models import Device
    from apps.monitoring.models import MonitoringCheck

    checks = device.checks.filter(is_active=True)
    if not checks.exists():
        return

    statuses = list(checks.values_list("current_status", flat=True))
    if all(s == MonitoringCheck.Status.UP for s in statuses):
        device.status = Device.Status.ONLINE
    elif all(s == MonitoringCheck.Status.DOWN for s in statuses):
        device.status = Device.Status.OFFLINE
    else:
        device.status = Device.Status.FAILED
    device.last_seen = timezone.now()
    device.save(update_fields=["status", "last_seen"])


@shared_task(queue="maintenance")
def cleanup_old_results(days=None):
    """Supprime les résultats de checks plus vieux que N jours, par lots.

    Sur la file `maintenance` et non la file par défaut : partager la file du flot de
    checks lui interdisait tout tour de parole, et la table avait atteint 1,9 M de
    lignes malgré une rétention déclarée. Par lots, parce qu'un seul `.delete()` sur
    ce volume charge toutes les clés en mémoire. La suppression est journalisée même
    quand elle est vide : une purge muette est indistinguable d'une purge absente.
    """
    from django.conf import settings

    from apps.monitoring.models import CheckResult

    days = days if days is not None else settings.MONITORING_RESULT_RETENTION_DAYS
    cutoff = timezone.now() - timezone.timedelta(days=days)
    batch = 10_000
    total = 0
    while True:
        ids = list(
            CheckResult.objects.filter(created_at__lt=cutoff).values_list("pk", flat=True)[:batch]
        )
        if not ids:
            break
        deleted, _ = CheckResult.objects.filter(pk__in=ids).delete()
        total += deleted
        if deleted < batch:
            break

    logger.info("Purge des résultats : %d supprimés (rétention %d jours)", total, days)
    return {"deleted": total, "days": days}
