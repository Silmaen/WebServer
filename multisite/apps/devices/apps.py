"""Configuration de l'application des appareils."""

from django.apps import AppConfig


class DevicesConfig(AppConfig):
    """Les appareils observés sur le réseau et leurs sondes."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.devices"
    verbose_name = "Appareils"
