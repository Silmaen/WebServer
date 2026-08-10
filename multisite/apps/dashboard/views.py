from django.db.models import Avg, Count
from django.views.generic import TemplateView

from apps.core.mixins import ViewerRequiredMixin
from apps.devices.models import Device


class DashboardView(ViewerRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        devices = Device.objects.all()
        ctx["total_devices"] = devices.count()
        ctx["online_count"] = devices.filter(status=Device.Status.ONLINE).count()
        ctx["offline_count"] = devices.filter(status=Device.Status.OFFLINE).count()
        ctx["failed_count"] = devices.filter(status=Device.Status.FAILED).count()
        ctx["unknown_category_count"] = devices.filter(category=Device.Category.UNKNOWN).count()
        ctx["by_category"] = (
            devices.values("category")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        ctx["recent_devices"] = devices.order_by("-updated_at")[:10]

        # Monitoring stats
        from apps.monitoring.models import MonitoringCheck, CheckResult

        checks = MonitoringCheck.objects.filter(is_active=True)
        ctx["total_checks"] = checks.count()
        ctx["checks_up"] = checks.filter(current_status=MonitoringCheck.Status.UP).count()
        ctx["checks_down"] = checks.filter(current_status=MonitoringCheck.Status.DOWN).count()
        ctx["checks_failing"] = checks.filter(current_status=MonitoringCheck.Status.FAILING).count()

        # Average response time (last hour)
        from django.utils import timezone
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        avg_rt = CheckResult.objects.filter(
            created_at__gte=one_hour_ago, response_time_ms__isnull=False
        ).aggregate(avg=Avg("response_time_ms"))
        ctx["avg_response_time"] = avg_rt["avg"]

        # Recent state changes (last 24h)
        one_day_ago = timezone.now() - timezone.timedelta(hours=24)
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
        state_changes = []
        prev_by_device = {}
        for ts, status, device_pk, hostname in results:
            prev = prev_by_device.get(device_pk)
            if prev is not None and status != prev:
                state_changes.append({
                    "time": ts,
                    "from": prev,
                    "to": status,
                    "device_pk": device_pk,
                    "hostname": hostname,
                })
            prev_by_device[device_pk] = status
        # Most recent first, limit to 5
        ctx["recent_state_changes"] = list(reversed(state_changes))[:5]

        # Top 5 slowest devices (by avg response time, last hour)
        ctx["slowest_checks"] = (
            CheckResult.objects.filter(created_at__gte=one_hour_ago, response_time_ms__isnull=False)
            .values("monitoring_check__device__hostname", "monitoring_check__device__pk", "monitoring_check__name")
            .annotate(avg_ms=Avg("response_time_ms"))
            .order_by("-avg_ms")[:5]
        )

        return ctx
