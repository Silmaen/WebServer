from django.contrib import admin
from .models import MonitoringCheck, CheckResult


@admin.register(MonitoringCheck)
class MonitoringCheckAdmin(admin.ModelAdmin):
    list_display = ["name", "device", "check_type", "current_status", "is_active", "interval", "last_checked"]
    list_filter = ["check_type", "current_status", "is_active"]
    search_fields = ["name", "device__hostname", "device__ip_address"]
    readonly_fields = ["current_status", "last_checked", "consecutive_failures", "created_at", "updated_at"]


@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    list_display = ["monitoring_check", "status", "response_time_ms", "created_at"]
    list_filter = ["status"]
    readonly_fields = ["monitoring_check", "status", "response_time_ms", "output", "error", "created_at"]
