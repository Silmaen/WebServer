"""Admin Django des réseaux et de leurs passerelles (debug uniquement)."""

from django.contrib import admin

from .models import GatewayCredential, Network


@admin.register(GatewayCredential)
class GatewayCredentialAdmin(admin.ModelAdmin):
    """Consultation des identifiants de passerelle."""

    list_display = ["name", "username", "use_https"]


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    """Consultation et réglage des réseaux à scanner."""

    list_display = ["name", "cidr", "vlan_id", "gateway", "gateway_credential", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "cidr"]
