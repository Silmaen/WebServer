"""Endpoints JSON de la console, consommés par les graphiques des gabarits."""

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.devices.models import Device
from apps.monitoring.history import transitions
from apps.monitoring.models import CheckResult, MonitoringCheck


class HealthCheckView(APIView):
    """Sonde de vivacité, ouverte : utilisée par le healthcheck du conteneur."""

    permission_classes = []

    def get(self, request):
        """Répond toujours `{"status": "ok"}` si Django tourne."""
        return Response({"status": "ok"})


class MonitoringTimeSeriesView(APIView):
    """Série temporelle : nombre d'appareils UP dans le temps, par tranches."""

    # période → (fenêtre en secondes, largeur d'une tranche en secondes).
    PERIODS = {
        "1h": (3600, 60),
        "6h": (21600, 300),
        "24h": (86400, 900),
        "7d": (604800, 3600),
        "30d": (2592000, 14400),
    }

    def get(self, request):
        """Renvoie les tranches, les transitions et les compteurs courants."""
        period = request.query_params.get("period", "24h")
        window_secs, bucket_secs = self.PERIODS.get(period, self.PERIODS["24h"])
        start = timezone.now() - timezone.timedelta(seconds=window_secs)

        device_qs = self._filtrer_appareils(request)
        target_device_ids = set(device_qs.values_list("pk", flat=True))
        if not target_device_ids:
            return Response({"buckets": [], "total_devices": 0})

        results = (
            CheckResult.objects.filter(
                created_at__gte=start,
                monitoring_check__device_id__in=target_device_ids,
            )
            .values("created_at", "status", "monitoring_check__device_id")
            .order_by("created_at")
        )

        buckets, par_appareil = self._repartir(results, bucket_secs)
        return Response({
            "buckets": self._series(buckets),
            "total_devices": len(target_device_ids),
            "period": period,
            "state_changes": self._changements(par_appareil, device_qs),
            "stats": self._stats(target_device_ids),
        })

    @staticmethod
    def _filtrer_appareils(request):
        """Les appareils visés, filtrés par catégorie et par identifiant."""
        categories = request.query_params.get("categories", "")
        device_ids = request.query_params.get("devices", "")
        qs = Device.objects.all()
        if categories:
            qs = qs.filter(category__in=categories.split(","))
        if device_ids:
            qs = qs.filter(pk__in=device_ids.split(","))
        return qs

    @staticmethod
    def _repartir(results, bucket_secs):
        """Répartit les résultats en tranches et en suites par appareil.

         :return : (tranches indexées par horodatage ISO, {appareil: [(date, état)]}).
        """
        buckets = {}
        par_appareil = {}
        for result in results:
            moment = result["created_at"]
            bucket_epoch = (int(moment.timestamp()) // bucket_secs) * bucket_secs
            key = timezone.datetime.fromtimestamp(bucket_epoch, tz=moment.tzinfo).isoformat()
            tranche = buckets.setdefault(
                key, {"up": set(), "down": set(), "failing": set(), "all": set()},
            )

            device_id = str(result["monitoring_check__device_id"])
            status = result["status"]
            tranche["all"].add(device_id)
            if status == "up":
                tranche["up"].add(device_id)
            elif status == "failing":
                tranche["failing"].add(device_id)
            else:
                tranche["down"].add(device_id)

            par_appareil.setdefault(device_id, []).append((moment, status))
        return buckets, par_appareil

    @staticmethod
    def _series(buckets):
        """Les tranches remises à plat, dans l'ordre chronologique."""
        return [
            {
                "t": key,
                "up": len(buckets[key]["up"]),
                "down": len(buckets[key]["down"]),
                "failing": len(buckets[key]["failing"]),
                "total": len(buckets[key]["all"]),
            }
            for key in sorted(buckets)
        ]

    @staticmethod
    def _changements(par_appareil, device_qs):
        """Les appareils ayant changé d'état, le changement le plus récent d'abord."""
        appareils = {
            str(d.pk): d for d in device_qs.only("pk", "hostname", "ip_address", "category")
        }
        changements = []
        for device_id, statuses in par_appareil.items():
            statuses.sort(key=lambda couple: couple[0])
            changes = [
                {"time": change["time"].isoformat(), "from": change["from"], "to": change["to"]}
                for change in transitions(statuses)
            ]
            appareil = appareils.get(device_id)
            if changes and appareil is not None:
                changements.append({
                    "id": device_id,
                    "hostname": appareil.hostname,
                    "ip": appareil.ip_address,
                    "category": appareil.category,
                    "changes": changes,
                    "current": statuses[-1][1],
                })
        changements.sort(key=lambda row: row["changes"][-1]["time"], reverse=True)
        return changements

    @staticmethod
    def _stats(target_device_ids):
        """Les compteurs courants, lus sur les checks actifs."""
        active_checks = MonitoringCheck.objects.filter(
            is_active=True, device_id__in=target_device_ids,
        )
        return {
            "total": active_checks.count(),
            "up": active_checks.filter(current_status="up").count(),
            "down": active_checks.filter(current_status="down").count(),
            "failing": active_checks.filter(current_status="failing").count(),
        }


class DeviceListAPIView(APIView):
    """Liste des appareils, pour les listes déroulantes de filtrage."""

    def get(self, request):
        """Renvoie les appareils, filtrés par catégorie si demandé."""
        category = request.query_params.get("category", "")
        qs = Device.objects.all().order_by("hostname")
        if category:
            qs = qs.filter(category__in=category.split(","))
        return Response([
            {"id": str(d.pk), "hostname": d.hostname, "category": d.category, "ip": d.ip_address}
            for d in qs
        ])
