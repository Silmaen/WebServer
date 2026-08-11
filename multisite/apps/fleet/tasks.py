"""Entretien périodique des tables de la flotte.

Une seule tâche, et elle supprime : cette base a déjà appris ce que coûte une table
d'historique sans borne. Elle tourne sur la file `maintenance` et non la file par
défaut, pour la raison qu'expose `apps/monitoring/tasks.py` — une purge qui partage
la file du flot de checks n'a jamais son tour de parole.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Report

logger = logging.getLogger("apps.fleet")


@shared_task(queue="maintenance")
def cleanup_old_reports():
    """Supprime les rapports plus vieux que `FLEET_REPORT_RETENTION_DAYS`.

    La rétention décide de la profondeur des tendances d'occupation disque, seule
    raison de garder les rapports au-delà du plus récent.
    """
    cutoff = timezone.now() - timezone.timedelta(days=settings.FLEET_REPORT_RETENTION_DAYS)
    deleted, _ = Report.objects.filter(at__lt=cutoff).delete()
    if deleted:
        logger.info("rapports purgés : %d antérieurs à %s", deleted, cutoff.date())
    return {"deleted": deleted}
