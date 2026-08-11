"""Modèles socles de la console : base horodatée et tâches d'arrière-plan."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Base abstraite : clé primaire UUID et dates de création / modification."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta data"""
        abstract = True


class BackgroundTask(models.Model):
    """Une tâche Celery suivie, avec son état, son résultat et son journal."""

    class Status(models.TextChoices):
        """États possibles d'une tâche."""
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
    log = models.TextField(blank=True, help_text="Journal d'exécution")
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="background_tasks",
        help_text="Utilisateur déclencheur (vide = automatique)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta data"""
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def append_log(self, message, level="INFO"):
        """Ajoute une ligne horodatée au journal de la tâche."""
        ts = timezone.now().strftime("%H:%M:%S")
        line = f"[{ts}] {level} {message}\n"
        # Concat en base plutôt qu'en Python : évite d'écraser les ajouts concurrents.
        BackgroundTask.objects.filter(pk=self.pk).update(log=Concat("log", Value(line)))

    @property
    def duration(self):
        """Durée écoulée, ou en cours si la tâche n'est pas terminée."""
        end = self.completed_at or timezone.now()
        start = self.started_at or self.created_at
        return end - start

    @classmethod
    def active_count(cls):
        """Nombre de tâches en attente ou en cours."""
        return cls.objects.filter(status__in=[cls.Status.PENDING, cls.Status.RUNNING]).count()

    @classmethod
    def cleanup_old(cls, days=7):
        """Supprime les tâches terminées depuis plus de `days` jours."""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        cls.objects.filter(completed_at__lt=cutoff).delete()
