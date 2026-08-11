"""Configuration de l'application de supervision."""

from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    """Les checks périodiques sur les appareils observés."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.monitoring"
    verbose_name = "Supervision"
