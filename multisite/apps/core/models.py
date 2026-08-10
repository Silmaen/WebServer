import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BackgroundTask(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        RUNNING = "running", "En cours"
        SUCCESS = "success", "Terminé"
        FAILURE = "failure", "Échoué"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    celery_task_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(blank=True)
    log = models.TextField(blank=True, help_text="Execution log")
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="background_tasks", help_text="User who triggered this task (null = automatic)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def append_log(self, message, level="INFO"):
        """Append a timestamped line to the task log."""
        ts = timezone.now().strftime("%H:%M:%S")
        line = f"[{ts}] {level} {message}\n"
        # Use F() to avoid race conditions with concurrent appends
        from django.db.models import Value
        from django.db.models.functions import Concat
        BackgroundTask.objects.filter(pk=self.pk).update(
            log=Concat("log", Value(line))
        )

    @property
    def duration(self):
        end = self.completed_at or timezone.now()
        start = self.started_at or self.created_at
        return end - start

    @classmethod
    def active_count(cls):
        return cls.objects.filter(status__in=[cls.Status.PENDING, cls.Status.RUNNING]).count()

    @classmethod
    def cleanup_old(cls, days=7):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        cls.objects.filter(completed_at__lt=cutoff).delete()
