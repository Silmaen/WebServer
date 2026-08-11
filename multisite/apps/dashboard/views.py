"""Vue d'ensemble de la console : compteurs, graphiques et derniers changements."""

from django.db.models import Avg, Count
from django.utils import timezone
from django.views.generic import TemplateView

from apps.core.mixins import ConsolePageMixin, ViewerRequiredMixin
from apps.devices.models import Device
from apps.monitoring.history import transitions_par_appareil
from apps.monitoring.models import CheckResult, MonitoringCheck


class DashboardView(ViewerRequiredMixin, ConsolePageMixin, TemplateView):
    """Vue d'ensemble de la console : compteurs, graphiques et derniers changements."""

    template_name = "dashboard/index.html"
    page_title = "Tableau de bord"

    def get_context_data(self, **kwargs):
        """Assemble les compteurs d'appareils, l'état des checks et l'historique."""
        ctx = super().get_context_data(**kwargs)
        ctx.update(self._appareils())
        ctx.update(self._supervision())
        return ctx

    @staticmethod
    def _appareils():
        """Compteurs et répartition des appareils."""
        devices = Device.objects.all()
        by_category = devices.values("category").annotate(count=Count("id")).order_by("-count")
        return {
            "total_devices": devices.count(),
            "online_count": devices.filter(status=Device.Status.ONLINE).count(),
            "offline_count": devices.filter(status=Device.Status.OFFLINE).count(),
            "failed_count": devices.filter(status=Device.Status.FAILED).count(),
            "unknown_category_count": devices.filter(category=Device.Category.UNKNOWN).count(),
            "by_category": by_category,
            # Sérialisable pour `json_script` : le gabarit passe les données au
            # graphique par le DOM.
            "category_chart_data": [
                {"label": row["category"], "count": row["count"]} for row in by_category
            ],
            "recent_devices": devices.order_by("-updated_at")[:10],
        }

    @staticmethod
    def _supervision():
        """État des checks, temps de réponse et changements des dernières 24 h."""
        checks = MonitoringCheck.objects.filter(is_active=True)
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        one_day_ago = timezone.now() - timezone.timedelta(hours=24)

        # Historique des changements d'état, reconstruit depuis les résultats.
        results = (
            CheckResult.objects.filter(created_at__gte=one_day_ago)
            .select_related("monitoring_check__device")
            .order_by("created_at")
            .values_list(
                "created_at", "status",
                "monitoring_check__device__pk",
                "monitoring_check__device__hostname",
            )
        )
        state_changes = [
            {
                "time": change["time"], "from": change["from"], "to": change["to"],
                "device_pk": change["device"], "hostname": change["extra"][0],
            }
            for change in transitions_par_appareil(results)
        ]

        recents = CheckResult.objects.filter(
            created_at__gte=one_hour_ago, response_time_ms__isnull=False,
        )
        return {
            "total_checks": checks.count(),
            "checks_up": checks.filter(current_status=MonitoringCheck.Status.UP).count(),
            "checks_down": checks.filter(current_status=MonitoringCheck.Status.DOWN).count(),
            "checks_failing": checks.filter(current_status=MonitoringCheck.Status.FAILING).count(),
            "avg_response_time": recents.aggregate(avg=Avg("response_time_ms"))["avg"],
            # Les plus récents d'abord, limités à 5.
            "recent_state_changes": list(reversed(state_changes))[:5],
            "slowest_checks": (
                recents.values(
                    "monitoring_check__device__hostname",
                    "monitoring_check__device__pk",
                    "monitoring_check__name",
                )
                .annotate(avg_ms=Avg("response_time_ms"))
                .order_by("-avg_ms")[:5]
            ),
        }
