"""Pages des réseaux, des identifiants de passerelle et des lancements de scan."""

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import ConsolePageMixin, StaffRequiredMixin, ViewerRequiredMixin
from apps.core.tasks import dispatch_task

from .forms import GatewayCredentialForm
from .gateway import UbusClient
from .models import GatewayCredential, Network
from .tasks import discover_network_task, gateway_scan_task, quick_scan_task

# Les champs saisissables d'un réseau, partagés par l'ajout et la modification.
NETWORK_FIELDS = [
    "name", "cidr", "vlan_id", "gateway", "gateway_credential",
    "description", "scan_interval", "is_active",
]


class NetworkPageMixin(ConsolePageMixin):
    """Contexte commun aux pages réseau : entrée de navigation à surligner."""

    nav_page = "network:list"


# --- Réseaux : lecture pour tous les autorisés, écriture pour le staff ---

class NetworkListView(ViewerRequiredMixin, NetworkPageMixin, ListView):
    """Liste des réseaux et de leurs appareils."""

    model = Network
    template_name = "network/network_list.html"
    context_object_name = "networks"
    page_title = "Réseaux"

    def get_queryset(self):
        """Précharge la passerelle et les appareils, tous deux affichés."""
        return (
            super().get_queryset()
            .select_related("gateway_credential")
            .prefetch_related("devices")
        )


class NetworkDetailView(ViewerRequiredMixin, NetworkPageMixin, DetailView):
    """Détail d'un réseau et des appareils qui y ont été vus."""

    model = Network
    template_name = "network/network_detail.html"
    context_object_name = "network"

    def get_page_title(self):
        """Titre de la page : le nom du réseau."""
        return self.object.name

    def get_context_data(self, **kwargs):
        """Ajoute les appareils du réseau et le nombre de non classés."""
        ctx = super().get_context_data(**kwargs)
        ctx["devices"] = self.object.devices.all()
        ctx["unknown_count"] = self.object.devices.filter(category="unknown").count()
        return ctx


class NetworkCreateView(StaffRequiredMixin, NetworkPageMixin, CreateView):
    """Ajout d'un réseau."""

    model = Network
    template_name = "network/network_form.html"
    fields = NETWORK_FIELDS
    success_url = reverse_lazy("network:list")
    page_title = "Ajouter un réseau"


class NetworkUpdateView(StaffRequiredMixin, NetworkPageMixin, UpdateView):
    """Modification d'un réseau."""

    model = Network
    template_name = "network/network_form.html"
    fields = NETWORK_FIELDS
    success_url = reverse_lazy("network:list")

    def get_page_title(self):
        """Titre de la page : le réseau modifié."""
        return f"Modifier {self.object.name}"


class NetworkDeleteView(StaffRequiredMixin, NetworkPageMixin, DeleteView):
    """Suppression d'un réseau, avec confirmation."""

    model = Network
    template_name = "network/network_confirm_delete.html"
    success_url = reverse_lazy("network:list")
    page_title = "Supprimer un réseau"


# --- Identifiants de passerelle : staff uniquement ---

class GatewayCredentialListView(StaffRequiredMixin, NetworkPageMixin, ListView):
    """Liste des identifiants de passerelle enregistrés."""

    model = GatewayCredential
    template_name = "network/credential_list.html"
    context_object_name = "credentials"
    page_title = "Identifiants de passerelle (OpenWrt)"


class GatewayCredentialCreateView(StaffRequiredMixin, NetworkPageMixin, CreateView):
    """Ajout d'un jeu d'identifiants de passerelle."""

    model = GatewayCredential
    template_name = "network/credential_form.html"
    form_class = GatewayCredentialForm
    success_url = reverse_lazy("network:credential-list")
    page_title = "Ajouter un identifiant de passerelle"


class GatewayCredentialUpdateView(StaffRequiredMixin, NetworkPageMixin, UpdateView):
    """Modification d'un jeu d'identifiants de passerelle."""

    model = GatewayCredential
    template_name = "network/credential_form.html"
    form_class = GatewayCredentialForm
    success_url = reverse_lazy("network:credential-list")

    def get_page_title(self):
        """Titre de la page : l'identifiant modifié."""
        return f"Modifier {self.object.name}"


class GatewayCredentialDeleteView(StaffRequiredMixin, NetworkPageMixin, DeleteView):
    """Suppression d'un jeu d'identifiants, avec confirmation."""

    model = GatewayCredential
    template_name = "network/credential_confirm_delete.html"
    success_url = reverse_lazy("network:credential-list")
    page_title = "Supprimer un identifiant"


class GatewayCredentialTestView(StaffRequiredMixin, View):
    """Teste la connexion à une passerelle avec les identifiants enregistrés."""

    def post(self, request, pk):
        """Se connecte à la passerelle indiquée et rapporte le résultat."""
        credential = GatewayCredential.objects.get(pk=pk)
        gateway_ip = request.POST.get("gateway_ip", "")
        if not gateway_ip:
            messages.error(request, "Adresse IP de la gateway requise.")
            return HttpResponseRedirect(reverse("network:credential-list"))
        try:
            client = UbusClient(gateway_ip, credential, timeout=10)
            client.login()
            leases = client.get_dhcp_leases()
            messages.success(request, f"Connexion OK ! {len(leases)} baux DHCP trouvés.")
        except Exception as e:
            messages.error(request, f"Erreur de connexion : {e}")
        return HttpResponseRedirect(reverse("network:credential-list"))


# --- Actions de scan : staff uniquement ---

class NetworkScanView(StaffRequiredMixin, View):
    """Lance un scan réseau via Celery. `mode=full` pour un scan approfondi."""

    # mode → (tâche, libellé de la tâche, message affiché)
    MODES = {
        "full": (
            discover_network_task, "Scan complet",
            "Scan complet de {nom} lancé (ports + OS, peut prendre plusieurs minutes).",
        ),
        "gateway": (
            gateway_scan_task, "Gateway scan",
            "Interrogation de la gateway de {nom} lancée.",
        ),
        "quick": (
            quick_scan_task, "Scan rapide",
            "Scan rapide de {nom} lancé (détection de présence).",
        ),
    }

    def post(self, request, pk):
        """Programme le scan demandé, en se rabattant sur le scan rapide."""
        try:
            network = Network.objects.get(pk=pk)
        except Network.DoesNotExist:
            messages.error(request, "Réseau introuvable.")
            return HttpResponseRedirect(reverse("network:list"))

        if not network.is_active:
            messages.warning(request, f"Le réseau {network.name} est désactivé.")
            return HttpResponseRedirect(reverse("network:detail", args=[pk]))

        mode = request.POST.get("mode", "quick")
        if mode == "gateway" and not network.can_query_gateway:
            mode = "quick"
        task, libelle, message = self.MODES.get(mode, self.MODES["quick"])

        dispatch_task(
            task,
            args=[str(network.pk)],
            name=f"{libelle} {network.name} ({network.cidr})",
            user=request.user,
        )
        messages.success(request, message.format(nom=network.name))
        return HttpResponseRedirect(reverse("network:detail", args=[pk]))
