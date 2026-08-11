"""Admin Django de la flotte (debug uniquement)."""

from django.contrib import admin

from .models import Machine, Report, Stack


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    """Consultation des machines déclarées ; tout est en lecture seule."""

    list_display = ("name", "ip", "role", "os_family", "wake_order", "retired")
    list_filter = ("retired", "os_family", "role")
    search_fields = ("name", "ip", "mac")
    # Miroir de _common/inventory.conf, qui reste la source de vérité : modifier une
    # ligne ici serait écrasé en silence par la prochaine synchronisation.
    readonly_fields = tuple(f.name for f in Machine._meta.fields)

    def has_add_permission(self, request):
        """Interdit la création : une machine naît dans l'inventaire, pas ici."""
        return False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Consultation de l'historique des rapports postés par les machines."""

    list_display = ("machine", "at", "drift_status", "drift_count")
    list_filter = ("machine", "drift_status")
    date_hierarchy = "at"


@admin.register(Stack)
class StackAdmin(admin.ModelAdmin):
    """Consultation des stacks compose déployées."""

    list_display = (
        "machine", "project", "repo", "head", "worktree", "behind", "compose", "last_seen",
    )
    list_filter = ("machine", "compose", "worktree")
    search_fields = ("project", "path", "remote")
