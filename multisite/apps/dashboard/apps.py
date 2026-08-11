"""Configuration de l'application du tableau de bord."""

from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """La vue d'ensemble de la console, sans modèle propre."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.dashboard"
    verbose_name = "Tableau de bord"
