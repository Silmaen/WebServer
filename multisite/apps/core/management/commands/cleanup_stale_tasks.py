"""Marque comme échouées les tâches restées en attente après un redémarrage."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import BackgroundTask


class Command(BaseCommand):
    """Referme les tâches orphelines : le worker qui les portait a disparu."""

    help = "Marque les tâches en attente ou en cours comme échouées (orphelines après redémarrage)."

    def handle(self, *args, **options):
        """Referme toutes les tâches encore ouvertes."""
        stale = BackgroundTask.objects.filter(
            status__in=[BackgroundTask.Status.PENDING, BackgroundTask.Status.RUNNING],
        )
        count = stale.count()
        if count == 0:
            self.stdout.write("Aucune tâche orpheline.")
            return

        stale.update(
            status=BackgroundTask.Status.FAILURE,
            error="Interrompue par un redémarrage du service",
            completed_at=timezone.now(),
        )
        self.stdout.write(self.style.SUCCESS(f"{count} tâche(s) orpheline(s) refermée(s)."))
