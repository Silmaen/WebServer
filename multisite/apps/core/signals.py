"""Report de l'état des tâches Celery sur les lignes `BackgroundTask`."""

from celery.signals import task_failure, task_prerun, task_success
from django.utils import timezone


@task_prerun.connect
def task_started_handler(sender=None, task_id=None, **kwargs):
    """Marque la tâche comme en cours quand le worker la prend."""
    # Importé ici : les signaux sont connectés depuis `AppConfig.ready()`.
    from apps.core.models import BackgroundTask

    BackgroundTask.objects.filter(celery_task_id=task_id).update(
        status=BackgroundTask.Status.RUNNING,
        started_at=timezone.now(),
    )


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Enregistre le résultat d'une tâche réussie."""
    from apps.core.models import BackgroundTask

    task_id = sender.request.id
    BackgroundTask.objects.filter(celery_task_id=task_id).update(
        status=BackgroundTask.Status.SUCCESS,
        result=result if isinstance(result, (dict, list)) else {"result": str(result)},
        completed_at=timezone.now(),
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """Enregistre l'erreur d'une tâche échouée."""
    from apps.core.models import BackgroundTask

    BackgroundTask.objects.filter(celery_task_id=task_id).update(
        status=BackgroundTask.Status.FAILURE,
        error=str(exception) if exception else "Erreur inconnue",
        completed_at=timezone.now(),
    )
