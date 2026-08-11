"""Page de supervision des appareils."""

from django.views.generic import TemplateView

from apps.core.mixins import ConsolePageMixin, ViewerRequiredMixin
from apps.devices.models import Device

from .models import MonitoringCheck


class MonitoringDashboardView(ViewerRequiredMixin, ConsolePageMixin, TemplateView):
    """Historique de supervision : état des appareils dans le temps et transitions."""

    template_name = "monitoring/dashboard.html"
    page_title = "Supervision des appareils"

    def get_context_data(self, **kwargs):
        """Ajoute les filtres de la page et les compteurs de checks.

        Les séries temporelles sont chargées côté client depuis
        `api:monitoring-timeseries`, car elles dépendent de la période choisie.
        """
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Device.Category.choices
        ctx["devices"] = (
            Device.objects.filter(checks__is_active=True).distinct().order_by("hostname")
        )
        checks = MonitoringCheck.objects.filter(is_active=True)
        ctx["total_checks"] = checks.count()
        ctx["checks_up"] = checks.filter(current_status=MonitoringCheck.Status.UP).count()
        ctx["checks_down"] = checks.filter(current_status=MonitoringCheck.Status.DOWN).count()
        ctx["checks_failing"] = checks.filter(current_status=MonitoringCheck.Status.FAILING).count()
        return ctx
