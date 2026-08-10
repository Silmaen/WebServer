from django.db import models

from apps.core.models import TimeStampedModel


class Device(TimeStampedModel):
    class Category(models.TextChoices):
        SERVER = "server", "Serveur"
        NETWORK = "network", "Équipement réseau"
        AP = "ap", "Point d'accès"
        IOT = "iot", "IoT"
        PRINTER = "printer", "Imprimante"
        WORKSTATION = "workstation", "Poste de travail"
        PHONE = "phone", "Téléphone"
        CAMERA = "camera", "Caméra / Visiophone"
        OTHER = "other", "Autre"
        UNKNOWN = "unknown", "Inconnu"

    class Status(models.TextChoices):
        ONLINE = "online", "En ligne"
        OFFLINE = "offline", "Hors ligne"
        FAILED = "failed", "En erreur"

    hostname = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(unique=True)
    mac_address = models.CharField(max_length=17, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.UNKNOWN)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONLINE)
    manufacturer = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    network = models.ForeignKey(
        "network.Network", on_delete=models.SET_NULL, null=True, blank=True, related_name="devices"
    )
    open_ports = models.JSONField(default=list, blank=True, help_text="List of open ports found during discovery")
    last_seen = models.DateTimeField(null=True, blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["hostname"]

    def __str__(self):
        return f"{self.hostname} ({self.ip_address})"


class ConnectionLog(TimeStampedModel):
    """Tracks when a device is seen connecting or disconnecting from the network."""

    class Event(models.TextChoices):
        CONNECTED = "connected", "Connecté"
        DISCONNECTED = "disconnected", "Déconnecté"

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="connection_logs")
    event = models.CharField(max_length=15, choices=Event.choices)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17, blank=True)
    network = models.ForeignKey(
        "network.Network", on_delete=models.SET_NULL, null=True, blank=True, related_name="connection_logs"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["device", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.device.hostname} {self.event} @ {self.created_at:%Y-%m-%d %H:%M}"
