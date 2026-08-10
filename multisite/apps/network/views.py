from django.contrib import messages
from apps.core.mixins import ViewerRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from apps.core.mixins import StaffRequiredMixin

from .forms import GatewayCredentialForm
from .models import GatewayCredential, Network


# --- Network views (read = all users, write = staff) ---

class NetworkListView(ViewerRequiredMixin, ListView):
    model = Network
    template_name = "network/network_list.html"
    context_object_name = "networks"

    def get_queryset(self):
        return super().get_queryset().select_related("gateway_credential").prefetch_related("devices")


class NetworkDetailView(ViewerRequiredMixin, DetailView):
    model = Network
    template_name = "network/network_detail.html"
    context_object_name = "network"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["devices"] = self.object.devices.all()
        ctx["unknown_count"] = self.object.devices.filter(category="unknown").count()
        return ctx


class NetworkCreateView(StaffRequiredMixin, CreateView):
    model = Network
    template_name = "network/network_form.html"
    fields = ["name", "cidr", "vlan_id", "gateway", "gateway_credential", "description", "scan_interval", "is_active"]
    success_url = reverse_lazy("network:list")


class NetworkUpdateView(StaffRequiredMixin, UpdateView):
    model = Network
    template_name = "network/network_form.html"
    fields = ["name", "cidr", "vlan_id", "gateway", "gateway_credential", "description", "scan_interval", "is_active"]
    success_url = reverse_lazy("network:list")


class NetworkDeleteView(StaffRequiredMixin, DeleteView):
    model = Network
    template_name = "network/network_confirm_delete.html"
    success_url = reverse_lazy("network:list")


# --- Gateway credential views (staff only) ---

class GatewayCredentialListView(StaffRequiredMixin, ListView):
    model = GatewayCredential
    template_name = "network/credential_list.html"
    context_object_name = "credentials"


class GatewayCredentialCreateView(StaffRequiredMixin, CreateView):
    model = GatewayCredential
    template_name = "network/credential_form.html"
    form_class = GatewayCredentialForm
    success_url = reverse_lazy("network:credential-list")


class GatewayCredentialUpdateView(StaffRequiredMixin, UpdateView):
    model = GatewayCredential
    template_name = "network/credential_form.html"
    form_class = GatewayCredentialForm
    success_url = reverse_lazy("network:credential-list")


class GatewayCredentialDeleteView(StaffRequiredMixin, DeleteView):
    model = GatewayCredential
    template_name = "network/credential_confirm_delete.html"
    success_url = reverse_lazy("network:credential-list")


class GatewayCredentialTestView(StaffRequiredMixin, View):
    """Test connectivity to a gateway using stored credentials."""

    def post(self, request, pk):
        credential = GatewayCredential.objects.get(pk=pk)
        gateway_ip = request.POST.get("gateway_ip", "")
        if not gateway_ip:
            messages.error(request, "Adresse IP de la gateway requise.")
            return HttpResponseRedirect(reverse("network:credential-list"))
        try:
            from .gateway import UbusClient
            client = UbusClient(gateway_ip, credential, timeout=10)
            client.login()
            leases = client.get_dhcp_leases()
            messages.success(request, f"Connexion OK ! {len(leases)} baux DHCP trouvés.")
        except Exception as e:
            messages.error(request, f"Erreur de connexion : {e}")
        return HttpResponseRedirect(reverse("network:credential-list"))


# --- Scan actions (staff only) ---

class NetworkScanView(StaffRequiredMixin, View):
    """Trigger a network scan via Celery. ?mode=full for deep scan."""

    def post(self, request, pk):
        from apps.core.tasks import dispatch_task
        from .tasks import discover_network_task, gateway_scan_task, quick_scan_task

        try:
            network = Network.objects.get(pk=pk)
        except Network.DoesNotExist:
            messages.error(request, "Réseau introuvable.")
            return HttpResponseRedirect(reverse("network:list"))

        if not network.is_active:
            messages.warning(request, f"Le réseau {network.name} est désactivé.")
            return HttpResponseRedirect(reverse("network:detail", args=[pk]))

        mode = request.POST.get("mode", "quick")
        if mode == "full":
            dispatch_task(
                discover_network_task,
                args=[str(network.pk)],
                name=f"Scan complet {network.name} ({network.cidr})",
                user=request.user,
            )
            messages.success(request, f"Scan complet de {network.name} lancé (ports + OS, peut prendre plusieurs minutes).")
        elif mode == "gateway" and network.can_query_gateway:
            dispatch_task(
                gateway_scan_task,
                args=[str(network.pk)],
                name=f"Gateway scan {network.name}",
                user=request.user,
            )
            messages.success(request, f"Interrogation de la gateway de {network.name} lancée.")
        else:
            dispatch_task(
                quick_scan_task,
                args=[str(network.pk)],
                name=f"Scan rapide {network.name} ({network.cidr})",
                user=request.user,
            )
            messages.success(request, f"Scan rapide de {network.name} lancé (détection de présence).")

        return HttpResponseRedirect(reverse("network:detail", args=[pk]))
