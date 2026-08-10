import logging

from celery.signals import task_prerun, task_success, task_failure
from django.utils import timezone

logger = logging.getLogger("apps")


@task_prerun.connect
def task_started_handler(sender=None, task_id=None, **kwargs):
    from apps.core.models import BackgroundTask

    BackgroundTask.objects.filter(celery_task_id=task_id).update(
        status=BackgroundTask.Status.RUNNING,
        started_at=timezone.now(),
    )


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    from apps.core.models import BackgroundTask

    task_id = sender.request.id
    BackgroundTask.objects.filter(celery_task_id=task_id).update(
        status=BackgroundTask.Status.SUCCESS,
        result=result if isinstance(result, (dict, list)) else {"result": str(result)},
        completed_at=timezone.now(),
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    from apps.core.models import BackgroundTask

    BackgroundTask.objects.filter(celery_task_id=task_id).update(
        status=BackgroundTask.Status.FAILURE,
        error=str(exception) if exception else "Unknown error",
        completed_at=timezone.now(),
    )
