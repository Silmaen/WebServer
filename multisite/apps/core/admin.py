from django.contrib import admin

from .models import BackgroundTask


@admin.register(BackgroundTask)
class BackgroundTaskAdmin(admin.ModelAdmin):
    list_display = ["name", "status", "created_at", "started_at", "completed_at"]
    list_filter = ["status"]
    readonly_fields = ["celery_task_id", "name", "status", "result", "error", "created_at", "started_at", "completed_at"]
