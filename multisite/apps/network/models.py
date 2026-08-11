"""Les réseaux surveillés et les identifiants de leurs passerelles."""

from django.db import models

from apps.core.models import TimeStampedModel



class GatewayCredential(TimeStampedModel):
    """Identifiants d'une passerelle OpenWrt, pour son API JSON-RPC ubus."""

    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, default="monitor")
    password = models.CharField(max_length=200)
    use_https = models.BooleanField(default=False)
    verify_ssl = models.BooleanField(
        default=False, help_text="Vérifier le certificat SSL (désactiver pour un auto-signé)",
    )

    class Meta:
        """Meta data"""
        ordering = ["name"]

    def __str__(self):
        return self.name


class Network(TimeStampedModel):
    """Un réseau à scanner : son CIDR, sa passerelle et son rythme de scan."""

    name = models.CharField(max_length=100)
    cidr = models.CharField(max_length=43, help_text="Notation CIDR, par ex. 192.168.1.0/24")
    vlan_id = models.PositiveIntegerField(null=True, blank=True)
    gateway = models.GenericIPAddressField(null=True, blank=True)
    gateway_credential = models.ForeignKey(
        GatewayCredential, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Identifiants de la passerelle (OpenWrt)",
    )
    description = models.TextField(blank=True)
    scan_interval = models.PositiveIntegerField(
        default=300, help_text="Intervalle de scan en secondes",
    )
    is_active = models.BooleanField(default=True)
    last_scan = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta data"""
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.cidr})"

    @property
    def can_query_gateway(self):
        """Ce réseau peut-il être scanné en interrogeant sa passerelle ?"""
        return bool(self.gateway and self.gateway_credential)
