from django.urls import path
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

app_name = "api"


class HealthCheckView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class MonitoringTimeSeriesView(APIView):
    """Time-series data: number of devices UP over time, bucketed."""

    PERIODS = {
        "1h": (3600, 60),          # 1h window, 1min buckets
        "6h": (21600, 300),         # 6h, 5min buckets
        "24h": (86400, 900),        # 24h, 15min buckets
        "7d": (604800, 3600),       # 7d, 1h buckets
        "30d": (2592000, 14400),    # 30d, 4h buckets
    }

    def get(self, request):
        from django.db.models import Count, Q
        from apps.monitoring.models import CheckResult
        from apps.devices.models import Device

        period = request.query_params.get("period", "24h")
        categories = request.query_params.get("categories", "")
        device_ids = request.query_params.get("devices", "")

        window_secs, bucket_secs = self.PERIODS.get(period, self.PERIODS["24h"])
        now = timezone.now()
        start = now - timezone.timedelta(seconds=window_secs)

        # Build device filter
        device_qs = Device.objects.all()
        if categories:
            device_qs = device_qs.filter(category__in=categories.split(","))
        if device_ids:
            device_qs = device_qs.filter(pk__in=device_ids.split(","))
        target_device_ids = set(device_qs.values_list("pk", flat=True))

        if not target_device_ids:
            return Response({"buckets": [], "total_devices": 0})

        # Fetch check results in the window for targeted devices
        results = (
            CheckResult.objects.filter(
                created_at__gte=start,
                monitoring_check__device_id__in=target_device_ids,
            )
            .values("created_at", "status", "monitoring_check__device_id")
            .order_by("created_at")
        )

        # Bucket the results and track per-device status sequences
        buckets = {}
        device_statuses = {}  # device_id -> list of (timestamp, status)
        for r in results:
            ts = r["created_at"]
            epoch = int(ts.timestamp())
            bucket_epoch = (epoch // bucket_secs) * bucket_secs
            key = timezone.datetime.fromtimestamp(bucket_epoch, tz=ts.tzinfo).isoformat()
            if key not in buckets:
                buckets[key] = {"up": set(), "down": set(), "failing": set(), "all": set()}
            device_id = str(r["monitoring_check__device_id"])
            buckets[key]["all"].add(device_id)
            status = r["status"]
            if status == "up":
                buckets[key]["up"].add(device_id)
            elif status == "failing":
                buckets[key]["failing"].add(device_id)
            else:
                buckets[key]["down"].add(device_id)

            # Track status sequence per device
            if device_id not in device_statuses:
                device_statuses[device_id] = []
            device_statuses[device_id].append((ts, r["status"]))

        # Convert to list
        series = []
        for ts_key in sorted(buckets.keys()):
            b = buckets[ts_key]
            series.append({
                "t": ts_key,
                "up": len(b["up"]),
                "down": len(b["down"]),
                "failing": len(b["failing"]),
                "total": len(b["all"]),
            })

        # Detect state changes: devices where status changed during period
        device_id_to_obj = {
            str(d.pk): d for d in device_qs.only("pk", "hostname", "ip_address", "category")
        }
        state_changes = []
        for dev_id, statuses in device_statuses.items():
            statuses.sort(key=lambda x: x[0])
            prev = None
            changes = []
            for ts, status in statuses:
                if prev is not None and status != prev:
                    changes.append({
                        "time": ts.isoformat(),
                        "from": prev,
                        "to": status,
                    })
                prev = status
            if changes and dev_id in device_id_to_obj:
                d = device_id_to_obj[dev_id]
                state_changes.append({
                    "id": dev_id,
                    "hostname": d.hostname,
                    "ip": d.ip_address,
                    "category": d.category,
                    "changes": changes,
                    "current": statuses[-1][1],
                })

        # Sort by most recent change first
        state_changes.sort(key=lambda x: x["changes"][-1]["time"], reverse=True)

        # Current stats from active checks
        from apps.monitoring.models import MonitoringCheck
        active_checks = MonitoringCheck.objects.filter(is_active=True, device_id__in=target_device_ids)
        stats = {
            "total": active_checks.count(),
            "up": active_checks.filter(current_status="up").count(),
            "down": active_checks.filter(current_status="down").count(),
            "failing": active_checks.filter(current_status="failing").count(),
        }

        return Response({
            "buckets": series,
            "total_devices": len(target_device_ids),
            "period": period,
            "state_changes": state_changes,
            "stats": stats,
        })


class DeviceListAPIView(APIView):
    """List devices for filter dropdowns."""

    def get(self, request):
        from apps.devices.models import Device
        category = request.query_params.get("category", "")
        qs = Device.objects.all().order_by("hostname")
        if category:
            qs = qs.filter(category__in=category.split(","))
        devices = [{"id": str(d.pk), "hostname": d.hostname, "category": d.category, "ip": d.ip_address}
                   for d in qs]
        return Response(devices)


urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("monitoring/timeseries/", MonitoringTimeSeriesView.as_view(), name="monitoring-timeseries"),
    path("devices/", DeviceListAPIView.as_view(), name="device-list"),
]
