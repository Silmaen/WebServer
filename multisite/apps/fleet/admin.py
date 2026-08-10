from django.contrib import admin

from .models import Machine, Report, Stack


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("name", "ip", "role", "os_family", "wake_order", "retired")
    list_filter = ("retired", "os_family", "role")
    search_fields = ("name", "ip", "mac")
    # Mirrored from _common/inventory.conf, which stays the source of truth: editing
    # a row here would be silently overwritten by the next sync.
    readonly_fields = tuple(f.name for f in Machine._meta.fields)

    def has_add_permission(self, request):
        return False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("machine", "at", "drift_status", "drift_count")
    list_filter = ("machine", "drift_status")
    date_hierarchy = "at"


@admin.register(Stack)
class StackAdmin(admin.ModelAdmin):
    list_display = ("machine", "project", "repo", "head", "worktree", "behind", "compose", "last_seen")
    list_filter = ("machine", "compose", "worktree")
    search_fields = ("project", "path", "remote")
