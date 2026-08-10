from django.db import models

from apps.core.models import TimeStampedModel


class GatewayCredential(TimeStampedModel):
    """Credentials for an OpenWrt gateway (ubus JSON-RPC API)."""

    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, default="monitor")
    password = models.CharField(max_length=200)
    use_https = models.BooleanField(default=False)
    verify_ssl = models.BooleanField(default=False, help_text="Verify SSL certificate (disable for self-signed)")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Network(TimeStampedModel):
    name = models.CharField(max_length=100)
    cidr = models.CharField(max_length=43, help_text="CIDR notation, e.g. 192.168.1.0/24")
    vlan_id = models.PositiveIntegerField(null=True, blank=True)
    gateway = models.GenericIPAddressField(null=True, blank=True)
    gateway_credential = models.ForeignKey(
        GatewayCredential, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="SSH credentials for the gateway (OpenWrt)",
    )
    description = models.TextField(blank=True)
    scan_interval = models.PositiveIntegerField(default=300, help_text="Scan interval in seconds")
    is_active = models.BooleanField(default=True)
    last_scan = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.cidr})"

    @property
    def can_query_gateway(self):
        return bool(self.gateway and self.gateway_credential)
