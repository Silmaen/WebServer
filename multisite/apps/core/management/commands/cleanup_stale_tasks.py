from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import BackgroundTask


class Command(BaseCommand):
    help = "Mark pending/running tasks as failed (orphaned after restart)."

    def handle(self, *args, **options):
        stale = BackgroundTask.objects.filter(
            status__in=[BackgroundTask.Status.PENDING, BackgroundTask.Status.RUNNING],
        )
        count = stale.count()
        if count == 0:
            self.stdout.write("No stale tasks found.")
            return

        now = timezone.now()
        stale.update(
            status=BackgroundTask.Status.FAILURE,
            error="Interrompue par un redémarrage du service",
            completed_at=now,
        )
        self.stdout.write(self.style.SUCCESS(f"Cleaned up {count} stale task(s)."))
