"""Configuration de l'application socle de la console."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Application socle : modèles partagés, permissions, suivi des tâches."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self):
        """Connecte les récepteurs de signaux Celery."""
        import apps.core.signals  # noqa: F401
