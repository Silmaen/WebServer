"""Configuration interne de l’application, injectée dans les gabarits."""
from pathlib import Path

APP_PATH = Path(__file__).parent
APP_NAME = APP_PATH.name

# Informations minimales communiquées à tout gabarit.
base_info = {
    "app_name": APP_NAME,
}
