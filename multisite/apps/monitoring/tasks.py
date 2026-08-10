import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("apps")


@shared_task
def schedule_due_checks():
    """Find checks that are due and dispatch them individually.

    The `update(last_checked=now)` before `.delay()` is the load-bearing line, and it
    is worth explaining because its absence cost months of silence.

    Beat calls this every 15 s, while a check's own interval is 300 s. Deciding
    whether a check is due from `last_checked`, when `last_checked` only moved once
    the task had *executed*, meant that every pass re-queued the checks that were
    already waiting in the queue. The deeper the backlog, the more duplicates each
    pass added: the queue had reached 5 670 messages and never drained, so anything
    else sharing it starved -- notably `cleanup_old_results`, which is why the
    results table had grown to 1.9 M rows with a 30-day retention declared.

    Claiming the check at dispatch time makes a queued check ineligible until its
    interval has passed again. The trade is that a check lost to a worker crash
    waits one interval instead of being retried at once, which is the right way
    round: a missed ping is cheaper than a queue that eats itself.
    """
    from apps.monitoring.models import MonitoringCheck

    now = timezone.now()
    due_checks = MonitoringCheck.objects.filter(is_active=True).select_related("device")

    dispatched = 0
    for check in due_checks:
        if check.last_checked is not None and (now - check.last_checked).total_seconds() < check.interval:
            continue
        MonitoringCheck.objects.filter(pk=check.pk).update(last_checked=now)
        execute_check.delay(str(check.pk))
        dispatched += 1

    if dispatched:
        logger.info("Dispatched %d due checks", dispatched)


@shared_task
def execute_check(check_id: str):
    """Execute a single monitoring check and store the result."""
    from apps.monitoring.checks import run_check
    from apps.monitoring.models import CheckResult, MonitoringCheck

    try:
        check = MonitoringCheck.objects.select_related("device").get(pk=check_id)
    except MonitoringCheck.DoesNotExist:
        logger.error("Check %s not found", check_id)
        return

    output = run_check(check.check_type, check.device.ip_address, check.config, check.timeout)

    # Update check status
    now = timezone.now()
    check.last_checked = now
    if output.success:
        check.current_status = MonitoringCheck.Status.UP
        check.consecutive_failures = 0
        result_status = CheckResult.Status.UP
    else:
        check.consecutive_failures += 1
        if check.consecutive_failures >= 3:
            check.current_status = MonitoringCheck.Status.DOWN
            result_status = CheckResult.Status.DOWN
        else:
            check.current_status = MonitoringCheck.Status.FAILING
            result_status = CheckResult.Status.FAILING
    check.save(update_fields=["current_status", "last_checked", "consecutive_failures"])

    # Store result with resolved status (up/down/failing)
    result = CheckResult.objects.create(
        monitoring_check=check,
        status=result_status,
        response_time_ms=output.response_time_ms,
        output=output.output,
        error=output.error,
    )

    # Update device status based on all its checks
    _update_device_status(check.device)

    logger.info("Check %s (%s): %s in %.1fms", check.name, check.device.ip_address, output.status, output.response_time_ms or 0)

    return {"check_id": str(check.pk), "status": output.status, "response_time_ms": output.response_time_ms}


def _update_device_status(device):
    """Update device status based on its monitoring checks."""
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
    """Delete check results older than N days, in batches.

    Two things were wrong with the one-line version, and they compounded:

    * it shared the queue with `execute_check`, so it never got a turn (see
      `schedule_due_checks`). Hence `queue="maintenance"`, which the worker consumes
      alongside `celery`: kombu rotates between the queues, so one maintenance
      message is picked up promptly even behind a deep backlog of checks.
    * a single `.delete()` over the whole backlog loads every primary key into
      memory and builds one enormous transaction. By the time anyone noticed, that
      was 1.37 M rows -- the batching below is what makes the first catch-up run
      finish at all.

    It also logs when it deletes nothing, unlike before: a purge that silently does
    nothing is indistinguishable from one that is not running, which is exactly the
    confusion that let this rot.
    """
    from django.conf import settings

    from apps.monitoring.models import CheckResult

    days = days if days is not None else settings.MONITORING_RESULT_RETENTION_DAYS
    cutoff = timezone.now() - timezone.timedelta(days=days)
    batch = 10_000
    total = 0
    while True:
        ids = list(CheckResult.objects.filter(created_at__lt=cutoff).values_list("pk", flat=True)[:batch])
        if not ids:
            break
        deleted, _ = CheckResult.objects.filter(pk__in=ids).delete()
        total += deleted
        if deleted < batch:
            break

    logger.info("Purge des résultats : %d supprimés (rétention %d jours)", total, days)
    return {"deleted": total, "days": days}
