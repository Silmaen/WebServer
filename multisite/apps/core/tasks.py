"""Suivi des tâches Celery : journalisation et lancement tracé."""

import logging

from django.utils import timezone

from apps.core.models import BackgroundTask

logger = logging.getLogger("apps")


class TaskLogger:
    """Écrit à la fois dans le logging Python et dans `BackgroundTask.log`.

    Usage dans une tâche Celery liée (`bind=True`) :
        tlog = TaskLogger(self)
        tlog.start()
        tlog.info("...")
    """

    def __init__(self, celery_task_instance):
        self._task_id = getattr(celery_task_instance, "request", None)
        self._bg_task = None

    @property
    def bg_task(self):
        """La ligne `BackgroundTask` de cette tâche, chargée à la demande."""
        if self._bg_task is None and self._task_id:
            task_id = self._task_id.id if hasattr(self._task_id, "id") else str(self._task_id)
            try:
                self._bg_task = BackgroundTask.objects.get(celery_task_id=task_id)
            except BackgroundTask.DoesNotExist:
                pass
        return self._bg_task

    def _log(self, level, message):
        """Écrit une ligne dans les deux journaux."""
        getattr(logger, level.lower(), logger.info)(message)
        if self.bg_task:
            self.bg_task.append_log(message, level)

    def info(self, msg, *args):
        """Journalise un message d'information."""
        self._log("INFO", msg % args if args else msg)

    def warning(self, msg, *args):
        """Journalise un avertissement."""
        self._log("WARNING", msg % args if args else msg)

    def error(self, msg, *args):
        """Journalise une erreur."""
        self._log("ERROR", msg % args if args else msg)

    def start(self):
        """Marque la tâche comme en cours."""
        if self.bg_task:
            self.bg_task.status = BackgroundTask.Status.RUNNING
            self.bg_task.started_at = timezone.now()
            self.bg_task.save(update_fields=["status", "started_at"])
            self.info("Tâche démarrée")

    def success(self, result=None):
        """Marque la tâche comme réussie et enregistre son résultat."""
        if self.bg_task:
            self.info("Tâche terminée avec succès")
            BackgroundTask.objects.filter(pk=self.bg_task.pk).update(
                status=BackgroundTask.Status.SUCCESS,
                result=result,
                completed_at=timezone.now(),
            )

    def failure(self, error_msg):
        """Marque la tâche comme échouée et enregistre l'erreur."""
        if self.bg_task:
            self.error("Tâche échouée: %s", error_msg)
            BackgroundTask.objects.filter(pk=self.bg_task.pk).update(
                status=BackgroundTask.Status.FAILURE,
                error=error_msg,
                completed_at=timezone.now(),
            )


def dispatch_task(celery_task, args=None, kwargs=None, name="", user=None):
    """Lance une tâche Celery et la trace comme `BackgroundTask`.

     :param celery_task : La tâche Celery à lancer.
     :param name : Le libellé affiché dans la console.
     :param user : L'utilisateur déclencheur ; None signifie automatique.
     :return : La `BackgroundTask` créée.
    """
    apply_kwargs = {}
    # Respecte la file déclarée sur la tâche.
    if hasattr(celery_task, "queue"):
        apply_kwargs["queue"] = celery_task.queue
    result = celery_task.apply_async(args=args or [], kwargs=kwargs or {}, **apply_kwargs)
    return BackgroundTask.objects.create(
        celery_task_id=result.id,
        name=name or celery_task.name,
        triggered_by=user,
    )
