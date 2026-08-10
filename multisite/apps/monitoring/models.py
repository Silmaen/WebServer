import uuid
from django.db import models
from apps.core.models import TimeStampedModel
from apps.devices.models import Device


class MonitoringCheck(TimeStampedModel):
    class CheckType(models.TextChoices):
        ICMP = "icmp", "Ping (ICMP)"
        TCP = "tcp", "Port TCP"
        HTTP = "http", "HTTP(S)"
        DNS = "dns", "DNS"

    class Status(models.TextChoices):
        UP = "up", "OK"
        DOWN = "down", "En panne"
        FAILING = "failing", "En erreur"
        UNKNOWN = "unknown", "Inconnu"

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="checks")
    name = models.CharField(max_length=200, blank=True)
    check_type = models.CharField(max_length=10, choices=CheckType.choices)
    is_active = models.BooleanField(default=True)
    interval = models.PositiveIntegerField(default=300, help_text="Intervalle en secondes")
    timeout = models.PositiveIntegerField(default=10, help_text="Timeout en secondes")
    config = models.JSONField(default=dict, blank=True, help_text="Configuration spécifique au type de check")
    current_status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNKNOWN)
    last_checked = models.DateTimeField(null=True, blank=True)
    consecutive_failures = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["device__hostname", "check_type"]

    def __str__(self):
        return self.name or f"{self.get_check_type_display()} - {self.device.hostname}"

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"{self.get_check_type_display()} - {self.device.hostname}"
        super().save(*args, **kwargs)


class CheckResult(TimeStampedModel):
    class Status(models.TextChoices):
        UP = "up", "OK"
        DOWN = "down", "En panne"
        FAILING = "failing", "En erreur"

    monitoring_check = models.ForeignKey(MonitoringCheck, on_delete=models.CASCADE, related_name="results")
    status = models.CharField(max_length=10, choices=Status.choices)
    response_time_ms = models.FloatField(null=True, blank=True)
    output = models.TextField(blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["monitoring_check", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.monitoring_check} - {self.status} ({self.created_at})"
