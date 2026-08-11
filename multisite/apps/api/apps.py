"""Configuration de l'application API de la console."""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Endpoints JSON consommés par les graphiques de la console."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api"
    verbose_name = "API"
