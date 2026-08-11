"""Configuration de l'application du site principal."""
from django.apps import AppConfig


class WwwConfig(AppConfig):
    """Le site public : articles, projets, bricolage, monitoring."""

    name = "www"
