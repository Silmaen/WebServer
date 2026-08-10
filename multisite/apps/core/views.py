from django.contrib import messages
from apps.core.mixins import ViewerRequiredMixin
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from .mixins import StaffRequiredMixin
from .models import BackgroundTask


class AdminDashboardView(StaffRequiredMixin, TemplateView):
    """Unified administration page."""
    template_name = "core/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        from apps.devices.models import Device
        from apps.monitoring.models import MonitoringCheck
        from apps.network.models import Network

        ctx = super().get_context_data(**kwargs)
        # Devices
        ctx["device_count"] = Device.objects.count()
        ctx["online_count"] = Device.objects.filter(status=Device.Status.ONLINE).count()
        ctx["offline_count"] = Device.objects.filter(status=Device.Status.OFFLINE).count()
        # Networks
        ctx["network_count"] = Network.objects.count()
        ctx["gateway_count"] = Network.objects.filter(
            gateway__isnull=False, gateway_credential__isnull=False,
        ).count()
        # Tasks
        ctx["task_active_count"] = BackgroundTask.objects.filter(
            status__in=[BackgroundTask.Status.PENDING, BackgroundTask.Status.RUNNING],
        ).count()
        ctx["task_total_count"] = BackgroundTask.objects.count()
        ctx["task_failed_count"] = BackgroundTask.objects.filter(
            status=BackgroundTask.Status.FAILURE,
        ).count()
        # Monitoring checks
        ctx["check_count"] = MonitoringCheck.objects.filter(is_active=True).count()
        ctx["check_up_count"] = MonitoringCheck.objects.filter(
            is_active=True, current_status=MonitoringCheck.Status.UP,
        ).count()
        ctx["check_down_count"] = MonitoringCheck.objects.filter(
            is_active=True, current_status=MonitoringCheck.Status.DOWN,
        ).count()
        return ctx


class AdminTasksPartialView(StaffRequiredMixin, View):
    """HTMX partial: tasks tab content."""

    def get(self, request):
        tasks = BackgroundTask.objects.select_related("triggered_by").order_by("-created_at")[:50]
        return TemplateResponse(request, "core/_admin_tasks.html", {"tasks": tasks})


class AdminCredentialsPartialView(StaffRequiredMixin, View):
    """HTMX partial: credentials tab content."""

    def get(self, request):
        from apps.network.models import GatewayCredential
        credentials = GatewayCredential.objects.prefetch_related("network_set").all()
        return TemplateResponse(request, "core/_admin_credentials.html", {"credentials": credentials})


class TaskIndicatorView(ViewerRequiredMixin, View):
    """HTMX partial: returns the task indicator badge for the navbar."""

    def get(self, request):
        active = BackgroundTask.objects.filter(
            status__in=[BackgroundTask.Status.PENDING, BackgroundTask.Status.RUNNING]
        )
        recent_done = BackgroundTask.objects.filter(
            status__in=[BackgroundTask.Status.SUCCESS, BackgroundTask.Status.FAILURE]
        ).order_by("-completed_at")[:5]

        return TemplateResponse(request, "includes/task_indicator.html", {
            "active_tasks": active,
            "recent_tasks": recent_done,
            "active_count": active.count(),
        })


class TaskListView(ViewerRequiredMixin, ListView):
    model = BackgroundTask
    template_name = "core/task_list.html"
    context_object_name = "tasks"
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().select_related("triggered_by")


class TaskDetailView(ViewerRequiredMixin, View):
    """Detailed view for a single task with logs."""

    def get(self, request, pk):
        from django.shortcuts import get_object_or_404
        task = get_object_or_404(BackgroundTask, pk=pk)

        # If HTMX request, return only the log partial
        if request.headers.get("HX-Request"):
            return TemplateResponse(request, "core/task_log_partial.html", {"task": task})

        return TemplateResponse(request, "core/task_detail.html", {"task": task})


class TaskRevokeView(StaffRequiredMixin, View):
    """Revoke/cancel a running or pending Celery task."""

    def post(self, request, pk):
        try:
            task = BackgroundTask.objects.get(pk=pk)
        except BackgroundTask.DoesNotExist:
            messages.error(request, "Tâche introuvable.")
            return HttpResponseRedirect(reverse("core:task-list"))

        if task.status not in (BackgroundTask.Status.PENDING, BackgroundTask.Status.RUNNING):
            messages.warning(request, f"La tâche « {task.name} » est déjà terminée.")
            return HttpResponseRedirect(reverse("core:task-list"))

        # Revoke the Celery task
        from config.celery import app as celery_app
        celery_app.control.revoke(task.celery_task_id, terminate=True, signal="SIGTERM")

        task.status = BackgroundTask.Status.FAILURE
        task.error = "Annulée par l'utilisateur"
        task.completed_at = timezone.now()
        task.save(update_fields=["status", "error", "completed_at"])

        messages.success(request, f"Tâche « {task.name} » annulée.")

        # If HTMX request, return the updated indicator
        if request.headers.get("HX-Request"):
            return TaskIndicatorView().get(request)

        return HttpResponseRedirect(reverse("core:task-list"))
