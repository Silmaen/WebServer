"""Configuration de l'application réseau."""

from django.apps import AppConfig


class NetworkConfig(AppConfig):
    """Les réseaux à scanner et la découverte des appareils."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.network"
    verbose_name = "Réseaux"
