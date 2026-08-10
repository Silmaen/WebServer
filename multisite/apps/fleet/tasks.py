"""Periodic upkeep for the fleet tables.

There is exactly one task and it deletes things. That is deliberate: this database
already learned what an unbounded history table costs — `monitoring_checkresult`
reached 1.9 M rows and `core_backgroundtask` 113 k, together 92 % of a 650 MB
database, for questions nobody asks about the past.

It runs on the `maintenance` queue rather than the default one, for the reason
`apps/monitoring/tasks.py` documents at length: a purge that shares a queue with a
check firehose never gets a turn, and a purge that never runs looks exactly like a
purge that is not configured.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Report

logger = logging.getLogger("apps.fleet")


@shared_task(queue="maintenance")
def cleanup_old_reports():
    """Drop reports older than `FLEET_REPORT_RETENTION_DAYS`.

    The retention is what decides how far back a disk-usage trend can be read, which
    is the one thing the reports are kept for beyond the latest row.
    """
    cutoff = timezone.now() - timezone.timedelta(days=settings.FLEET_REPORT_RETENTION_DAYS)
    deleted, _ = Report.objects.filter(at__lt=cutoff).delete()
    if deleted:
        logger.info("rapports purgés : %d antérieurs à %s", deleted, cutoff.date())
    return {"deleted": deleted}
