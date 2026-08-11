"""Pages transverses de la console : administration et suivi des tâches."""

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.devices.models import Device
from apps.monitoring.models import MonitoringCheck
from apps.network.models import GatewayCredential, Network

from .mixins import ConsolePageMixin, StaffRequiredMixin, ViewerRequiredMixin
from .models import BackgroundTask


class AdminDashboardView(StaffRequiredMixin, ConsolePageMixin, TemplateView):
    """Page d'administration unifiée de la console."""

    template_name = "core/admin_dashboard.html"
    page_title = "Administration de la console"

    def get_context_data(self, **kwargs):
        """Compteurs de la vue d'ensemble, puis les tâches et les identifiants.

        Les trois partiels de la page sont inclus directement, donc tout leur
        contexte est fourni ici.
        """
        ctx = super().get_context_data(**kwargs)
        # Appareils
        ctx["device_count"] = Device.objects.count()
        ctx["online_count"] = Device.objects.filter(status=Device.Status.ONLINE).count()
        ctx["offline_count"] = Device.objects.filter(status=Device.Status.OFFLINE).count()
        # Réseaux
        ctx["network_count"] = Network.objects.count()
        ctx["gateway_count"] = Network.objects.filter(
            gateway__isnull=False, gateway_credential__isnull=False,
        ).count()
        # Tâches
        ctx["task_active_count"] = BackgroundTask.objects.filter(
            status__in=[BackgroundTask.Status.PENDING, BackgroundTask.Status.RUNNING],
        ).count()
        ctx["task_total_count"] = BackgroundTask.objects.count()
        ctx["task_failed_count"] = BackgroundTask.objects.filter(
            status=BackgroundTask.Status.FAILURE,
        ).count()
        # Checks de supervision
        ctx["check_count"] = MonitoringCheck.objects.filter(is_active=True).count()
        ctx["check_up_count"] = MonitoringCheck.objects.filter(
            is_active=True, current_status=MonitoringCheck.Status.UP,
        ).count()
        ctx["check_down_count"] = MonitoringCheck.objects.filter(
            is_active=True, current_status=MonitoringCheck.Status.DOWN,
        ).count()
        # Contenu des deux sections empilées sous la vue d'ensemble.
        ctx["tasks"] = (
            BackgroundTask.objects.select_related("triggered_by").order_by("-created_at")[:50]
        )
        ctx["credentials"] = GatewayCredential.objects.prefetch_related("network_set").all()
        return ctx


class TaskListView(ViewerRequiredMixin, ConsolePageMixin, ListView):
    """Liste paginée des tâches d'arrière-plan."""

    model = BackgroundTask
    template_name = "core/task_list.html"
    context_object_name = "tasks"
    paginate_by = 50
    page_title = "Tâches en arrière-plan"

    def get_queryset(self):
        """Précharge l'utilisateur déclencheur, affiché dans chaque ligne."""
        return super().get_queryset().select_related("triggered_by")


class TaskDetailView(ViewerRequiredMixin, ConsolePageMixin, DetailView):
    """Détail d'une tâche et son journal."""

    model = BackgroundTask
    template_name = "core/task_detail.html"
    context_object_name = "task"

    def get_page_title(self):
        """Titre de la page : le nom de la tâche."""
        return self.object.name

    def get(self, request, *args, **kwargs):
        """Rafraîchissement HTMX : seul le journal est renvoyé."""
        if request.headers.get("HX-Request"):
            task = get_object_or_404(BackgroundTask, pk=kwargs["pk"])
            return TemplateResponse(request, "core/task_log_partial.html", {"task": task})
        return super().get(request, *args, **kwargs)


class TaskRevokeView(StaffRequiredMixin, View):
    """Annule une tâche Celery en attente ou en cours."""

    def post(self, request, pk):
        """Révoque la tâche côté Celery et marque la ligne comme échouée."""
        try:
            task = BackgroundTask.objects.get(pk=pk)
        except BackgroundTask.DoesNotExist:
            messages.error(request, "Tâche introuvable.")
            return HttpResponseRedirect(reverse("core:task-list"))

        if task.status not in (BackgroundTask.Status.PENDING, BackgroundTask.Status.RUNNING):
            messages.warning(request, f"La tâche « {task.name} » est déjà terminée.")
            return HttpResponseRedirect(reverse("core:task-list"))

        # Importé ici : `multisite.celery` construit l'application Celery, ce qui n'a
        # rien à faire au chargement des vues.
        from multisite.celery import app as celery_app
        celery_app.control.revoke(task.celery_task_id, terminate=True, signal="SIGTERM")

        task.status = BackgroundTask.Status.FAILURE
        task.error = "Annulée par l'utilisateur"
        task.completed_at = timezone.now()
        task.save(update_fields=["status", "error", "completed_at"])

        messages.success(request, f"Tâche « {task.name} » annulée.")
        return HttpResponseRedirect(reverse("core:task-list"))
