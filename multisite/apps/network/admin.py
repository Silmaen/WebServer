from django.contrib import admin

from .models import GatewayCredential, Network


@admin.register(GatewayCredential)
class GatewayCredentialAdmin(admin.ModelAdmin):
    list_display = ["name", "username", "use_https"]


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ["name", "cidr", "vlan_id", "gateway", "gateway_credential", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "cidr"]
