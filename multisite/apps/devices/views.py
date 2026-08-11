"""Pages des appareils découverts sur le réseau."""

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import ConsolePageMixin, StaffRequiredMixin, ViewerRequiredMixin
from apps.core.tasks import dispatch_task
from apps.monitoring.history import transitions
from apps.monitoring.models import CheckResult, MonitoringCheck

from .models import Device
from .tasks import deep_probe_task, quick_probe_task

# Les champs saisissables d'un appareil, partagés par l'ajout et la modification.
DEVICE_FIELDS = [
    "hostname", "ip_address", "mac_address", "category", "status",
    "manufacturer", "model", "description", "network",
]


class DevicePageMixin(ConsolePageMixin):
    """Contexte commun aux pages des appareils : entrée de navigation à surligner."""

    nav_page = "devices:list"


class DeviceListView(ViewerRequiredMixin, DevicePageMixin, ListView):
    """Liste des appareils, filtrable par catégorie, état et recherche libre."""

    model = Device
    template_name = "devices/device_list.html"
    context_object_name = "devices"
    paginate_by = 25
    page_title = "Appareils"

    def get_queryset(self):
        """Applique les filtres de l'URL à la liste."""
        qs = super().get_queryset().select_related("network")
        category = self.request.GET.get("category")
        status = self.request.GET.get("status")
        search = self.request.GET.get("q")
        if category:
            qs = qs.filter(category=category)
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(hostname__icontains=search) | qs.filter(ip_address__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        """Ajoute les choix de filtre et les valeurs courantes."""
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Device.Category.choices
        ctx["statuses"] = Device.Status.choices
        ctx["current_category"] = self.request.GET.get("category", "")
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["current_search"] = self.request.GET.get("q", "")
        return ctx


class DeviceDetailView(ViewerRequiredMixin, DevicePageMixin, DetailView):
    """Détail d'un appareil : historique d'état, connexions et checks actifs."""

    model = Device
    template_name = "devices/device_detail.html"
    context_object_name = "device"

    def get_page_title(self):
        """Titre de la page : le nom de l'appareil."""
        return self.object.hostname

    def get_context_data(self, **kwargs):
        """Ajoute l'historique d'état, le journal de connexion et les checks."""
        ctx = super().get_context_data(**kwargs)
        device = self.object

        # Historique des changements d'état, reconstruit depuis les résultats de checks.
        results = (
            CheckResult.objects.filter(monitoring_check__device=device)
            .order_by("created_at")
            .values_list("created_at", "status")
        )
        ctx["state_changes"] = list(reversed(transitions(results)))[:20]

        # Journal de connexion, alimenté par les scans réseau.
        ctx["connection_logs"] = (
            device.connection_logs.select_related("network").order_by("-created_at")[:20]
        )
        ctx["checks"] = MonitoringCheck.objects.filter(device=device, is_active=True)
        return ctx


class DeviceCreateView(StaffRequiredMixin, DevicePageMixin, CreateView):
    """Ajout manuel d'un appareil."""

    model = Device
    template_name = "devices/device_form.html"
    fields = DEVICE_FIELDS
    success_url = reverse_lazy("devices:list")
    page_title = "Ajouter un appareil"


class DeviceUpdateView(StaffRequiredMixin, DevicePageMixin, UpdateView):
    """Modification d'un appareil."""

    model = Device
    template_name = "devices/device_form.html"
    fields = DEVICE_FIELDS
    success_url = reverse_lazy("devices:list")

    def get_page_title(self):
        """Titre de la page : l'appareil modifié."""
        return f"Modifier {self.object.hostname}"


class DeviceDeleteView(StaffRequiredMixin, DevicePageMixin, DeleteView):
    """Suppression d'un appareil, avec confirmation."""

    model = Device
    template_name = "devices/device_confirm_delete.html"
    success_url = reverse_lazy("devices:list")
    page_title = "Supprimer un appareil"


class DeviceProbeView(StaffRequiredMixin, View):
    """Lance un scan de ports et une détection d'OS sur un appareil."""

    def post(self, request, pk):
        """Programme la sonde demandée (`quick` par défaut, ou `deep`)."""
        device = get_object_or_404(Device, pk=pk)
        mode = request.POST.get("mode", "quick")
        task = deep_probe_task if mode == "deep" else quick_probe_task
        libelle = "Deep probe" if mode == "deep" else "Quick probe"
        dispatch_task(
            task,
            args=[str(device.pk)],
            name=f"{libelle} : {device.hostname}",
            user=request.user,
        )
        return redirect("devices:detail", pk=pk)
