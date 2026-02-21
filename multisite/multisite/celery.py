"""Configuration Celery pour le projet."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "multisite.settings")

app = Celery("multisite")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
