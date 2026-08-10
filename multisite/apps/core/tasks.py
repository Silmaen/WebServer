import logging

from django.utils import timezone

from apps.core.models import BackgroundTask

logger = logging.getLogger("apps")


class TaskLogger:
    """Logger that writes to both Python logging and BackgroundTask.log.

    Usage in a Celery task:
        tlog = TaskLogger(self)   # self is the bound Celery task
        tlog.info("Starting...")
        tlog.warning("Something odd")
        tlog.error("Failed!")
    """

    def __init__(self, celery_task_instance):
        self._task_id = getattr(celery_task_instance, "request", None)
        self._bg_task = None

    @property
    def bg_task(self):
        if self._bg_task is None and self._task_id:
            task_id = self._task_id.id if hasattr(self._task_id, "id") else str(self._task_id)
            try:
                self._bg_task = BackgroundTask.objects.get(celery_task_id=task_id)
            except BackgroundTask.DoesNotExist:
                pass
        return self._bg_task

    def _log(self, level, message):
        getattr(logger, level.lower(), logger.info)(message)
        if self.bg_task:
            self.bg_task.append_log(message, level)

    def info(self, msg, *args):
        self._log("INFO", msg % args if args else msg)

    def warning(self, msg, *args):
        self._log("WARNING", msg % args if args else msg)

    def error(self, msg, *args):
        self._log("ERROR", msg % args if args else msg)

    def start(self):
        """Mark the task as running."""
        if self.bg_task:
            self.bg_task.status = BackgroundTask.Status.RUNNING
            self.bg_task.started_at = timezone.now()
            self.bg_task.save(update_fields=["status", "started_at"])
            self.info("Tâche démarrée")

    def success(self, result=None):
        """Mark the task as succeeded."""
        if self.bg_task:
            self.info("Tâche terminée avec succès")
            BackgroundTask.objects.filter(pk=self.bg_task.pk).update(
                status=BackgroundTask.Status.SUCCESS,
                result=result,
                completed_at=timezone.now(),
            )

    def failure(self, error_msg):
        """Mark the task as failed."""
        if self.bg_task:
            self.error("Tâche échouée: %s", error_msg)
            BackgroundTask.objects.filter(pk=self.bg_task.pk).update(
                status=BackgroundTask.Status.FAILURE,
                error=error_msg,
                completed_at=timezone.now(),
            )


def dispatch_task(celery_task, args=None, kwargs=None, name="", user=None):
    """Dispatch a Celery task and track it as a BackgroundTask.

    Args:
        user: The user who triggered the task. None means automatic trigger.

    Returns the BackgroundTask instance.
    """
    task_kwargs = kwargs or {}
    apply_kwargs = {}
    # Respect queue defined on the task
    if hasattr(celery_task, "queue"):
        apply_kwargs["queue"] = celery_task.queue
    result = celery_task.apply_async(args=args or [], kwargs=task_kwargs, **apply_kwargs)
    task = BackgroundTask.objects.create(
        celery_task_id=result.id,
        name=name or celery_task.name,
        triggered_by=user,
    )
    return task
