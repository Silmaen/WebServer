from apps.core.mixins import ViewerRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from apps.core.mixins import StaffRequiredMixin

from .models import Device


class DeviceListView(ViewerRequiredMixin, ListView):
    model = Device
    template_name = "devices/device_list.html"
    context_object_name = "devices"
    paginate_by = 25

    def get_queryset(self):
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
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Device.Category.choices
        ctx["statuses"] = Device.Status.choices
        ctx["current_category"] = self.request.GET.get("category", "")
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["current_search"] = self.request.GET.get("q", "")
        return ctx


class DeviceDetailView(ViewerRequiredMixin, DetailView):
    model = Device
    template_name = "devices/device_detail.html"
    context_object_name = "device"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        device = self.object

        # Build state change history from check results
        from apps.monitoring.models import CheckResult
        results = (
            CheckResult.objects.filter(monitoring_check__device=device)
            .order_by("created_at")
            .values_list("created_at", "status")
        )
        state_changes = []
        prev_status = None
        for ts, status in results:
            if prev_status is not None and status != prev_status:
                state_changes.append({
                    "time": ts,
                    "from": prev_status,
                    "to": status,
                })
            prev_status = status
        ctx["state_changes"] = list(reversed(state_changes))[:20]

        # Connection log (populated by network scans)
        ctx["connection_logs"] = device.connection_logs.select_related("network").order_by("-created_at")[:20]

        # Monitoring checks for this device
        from apps.monitoring.models import MonitoringCheck
        ctx["checks"] = MonitoringCheck.objects.filter(device=device, is_active=True)

        return ctx


class DeviceCreateView(StaffRequiredMixin, CreateView):
    model = Device
    template_name = "devices/device_form.html"
    fields = ["hostname", "ip_address", "mac_address", "category", "status", "manufacturer", "model", "description", "network"]
    success_url = reverse_lazy("devices:list")


class DeviceUpdateView(StaffRequiredMixin, UpdateView):
    model = Device
    template_name = "devices/device_form.html"
    fields = ["hostname", "ip_address", "mac_address", "category", "status", "manufacturer", "model", "description", "network"]
    success_url = reverse_lazy("devices:list")


class DeviceDeleteView(StaffRequiredMixin, DeleteView):
    model = Device
    template_name = "devices/device_confirm_delete.html"
    success_url = reverse_lazy("devices:list")


class DeviceProbeView(StaffRequiredMixin, View):
    """Trigger a port scan + OS detection for a device."""

    def post(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        from apps.core.tasks import dispatch_task
        from apps.devices.tasks import deep_probe_task, quick_probe_task

        mode = request.POST.get("mode", "quick")
        if mode == "deep":
            dispatch_task(deep_probe_task, args=[str(device.pk)], name=f"Deep probe : {device.hostname}", user=request.user)
        else:
            dispatch_task(quick_probe_task, args=[str(device.pk)], name=f"Quick probe : {device.hostname}", user=request.user)
        return redirect("devices:detail", pk=pk)
