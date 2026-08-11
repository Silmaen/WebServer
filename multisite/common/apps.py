"""Configuration de l'application des modèles partagés."""
from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Modèles et utilitaires partagés par le site et la console."""

    name = "common"
