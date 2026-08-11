"""Configuration de l'application flotte."""

from django.apps import AppConfig


class FleetConfig(AppConfig):
    """Les machines déclarées du lab, leurs rapports et leurs stacks."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.fleet"
    verbose_name = "Flotte"
