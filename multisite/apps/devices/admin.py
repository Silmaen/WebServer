"""Admin Django des appareils observés (debug uniquement)."""

from django.contrib import admin

from .models import ConnectionLog, Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Consultation et correction manuelle des appareils découverts."""

    list_display = ["hostname", "ip_address", "category", "status", "network", "manufacturer"]
    list_filter = ["category", "status", "network"]
    search_fields = ["hostname", "ip_address", "mac_address", "manufacturer"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ConnectionLog)
class ConnectionLogAdmin(admin.ModelAdmin):
    """Journal des connexions et déconnexions relevées par les scans."""

    list_display = ["device", "event", "ip_address", "mac_address", "network", "created_at"]
    list_filter = ["event", "network", "created_at"]
    search_fields = ["device__hostname", "ip_address", "mac_address"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
