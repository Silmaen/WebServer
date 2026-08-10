from apps.core.mixins import ViewerRequiredMixin
from django.views.generic import TemplateView

from apps.devices.models import Device

from .models import MonitoringCheck


class MonitoringDashboardView(ViewerRequiredMixin, TemplateView):
    template_name = "monitoring/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Device.Category.choices
        ctx["devices"] = Device.objects.filter(
            checks__is_active=True
        ).distinct().order_by("hostname")
        checks = MonitoringCheck.objects.filter(is_active=True)
        ctx["total_checks"] = checks.count()
        ctx["checks_up"] = checks.filter(current_status=MonitoringCheck.Status.UP).count()
        ctx["checks_down"] = checks.filter(current_status=MonitoringCheck.Status.DOWN).count()
        ctx["checks_failing"] = checks.filter(current_status=MonitoringCheck.Status.FAILING).count()
        return ctx
