"""Réglages Django du projet multisite."""
import os
from pathlib import Path

# Les chemins du projet se construisent depuis BASE_DIR.
BASE_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = BASE_DIR.parent

# Voir https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# ATTENTION : la clé secrète de production ne doit jamais être publiée.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "(qu$15^l4oqf9d+^-lb-ih#^i3xoh+vn=#sp)u)&k_fli*sd64")

# ATTENTION : ne jamais laisser DEBUG actif en production.
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost,www.argawaen.net"
).split(",")

CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:8000,http://localhost:8000,https://www.argawaen.net"
).split(",")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.forms",
    "markdownx",  # Prise en charge des contenus Markdown.
    # Bibliothèques tierces, pour la console (apps.* plus bas)
    "rest_framework",
    "django_filters",
    "django_htmx",
    "django_celery_beat",
    "mozilla_django_oidc",
    "common.apps.CommonConfig",
    "www.apps.WwwConfig",
    "connector.apps.ConnectorConfig",
    # La console du homelab et la supervision réseau, venues de leurs propres dépôts.
    # Elles gardent le préfixe `apps.` à dessein : il préserve les app_labels des
    # migrations, donc la base existante se transporte au lieu d'être reconstruite.
    "apps.core",
    "apps.network",
    "apps.devices",
    "apps.monitoring",
    "apps.dashboard",
    "apps.fleet",
    "apps.api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "mozilla_django_oidc.middleware.SessionRefresh",
    "apps.core.middleware.InactiveUserMiddleware",
    # Après AuthenticationMiddleware, car il lit request.user. N'agit que sur un
    # navigateur déjà venu -- voir apps/core/sso.py.
    "apps.core.sso.SilentSSOMiddleware",
]

ROOT_URLCONF = "multisite.urls"

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            SITE_DIR / "data" / "templates" / "common",
            # La racine des gabarits de la console : ils se référencent entre eux sans
            # préfixe, et aucun de ces noms n'existe sous www/ ou common/.
            SITE_DIR / "data" / "templates" / "console",
            SITE_DIR / "data" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.sso",
                "www.context_processors.navigation",
            ],
        },
    },
]

WSGI_APPLICATION = "multisite.wsgi.application"

# Proxy — Django est derrière nginx
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

EMAIL_HOST = os.environ.get("EMAIL_HOST", "127.0.0.1")
EMAIL_PORT = os.environ.get("EMAIL_PORT", "587")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "site@argawaen.net")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "site")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")

# Email
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "webmaster@argawaen.net")

# Base de données
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "argawaen"),
        "USER": os.environ.get("DB_USER", "argawaen"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "argawaen"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    },
}

# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalisation
LANGUAGE_CODE = "fr"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_TZ = True


# Les fichiers statiques
STATIC_URL = "/static/"
STATICFILES_DIRS = [SITE_DIR / "data" / "static"]
STATIC_ROOT = SITE_DIR / "staticfiles"

# Les medias
MEDIA_URL = "/media/"
MEDIA_ROOT = SITE_DIR / "data" / "media"

# Login redirection
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Markdownx -- https://neutronx.github.io/django-markdownx/
MARKDOWNX_MARKDOWN_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.codehilite",
    "pymdownx.tasklist",
]
MARKDOWNX_MARKDOWN_EXTENSION_CONFIGS = {
    "markdown.extensions.codehilite": {
        "css_class": "codehilite",
        "guess_lang": True,
    },
    "pymdownx.tasklist": {
        "custom_checkbox": True,
    },
}

# Celery
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_ROUTES = {
    # Réservées au worker scanner : elles ont besoin du réseau de l'hôte et de NET_RAW.
    "apps.network.*": {"queue": "network"},
    "apps.devices.tasks.*": {"queue": "network"},
}
CELERY_BEAT_SCHEDULE = {
    # `maintenance` est une file à part, consommée en parallèle de `celery` : une purge
    # qui partage la file du flot de checks n'a jamais son tour de parole.

    "fleet-cleanup-old-reports": {
        "task": "apps.fleet.tasks.cleanup_old_reports",
        "schedule": 86400.0,
    },
    "schedule-due-checks": {
        "task": "apps.monitoring.tasks.schedule_due_checks",
        "schedule": 15.0,
    },
    "schedule-due-scans": {
        "task": "apps.network.tasks.schedule_due_scans",
        "schedule": 60.0,
    },
    "schedule-device-probes": {
        "task": "apps.devices.tasks.schedule_device_probes",
        "schedule": 3600.0,
    },
    "cleanup-old-results": {
        "task": "apps.monitoring.tasks.cleanup_old_results",
        "schedule": 86400.0,
    },
}

# www.tasks.verifier_machines et verifier_serveurs ne sont plus planifiés : un seul
# moteur de checks, celui de apps.monitoring. Les fonctions restent dans www/tasks.py,
# qui porte aussi les générateurs SSE appelés à la demande par les vues.

# Monitoring
MONITORING_DOMAINE_DEFAUT = os.environ.get("MONITORING_DOMAINE_DEFAUT", "")


# --- La console du homelab, venue de son propre dépôt ----------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "apps.core.permissions.IsViewer",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

# Le site est délibérément public, donc authentik ne peut pas filtrer le vhost : c'est
# de l'OIDC *dans* Django. Le ModelBackend local reste le repli si authentik tombe.
AUTHENTICATION_BACKENDS = [
    "apps.core.auth.OIDCAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# La page de connexion du site, par nom d'URL : un site, une connexion.
LOGIN_URL = "login"

OIDC_ENABLED = bool(os.environ.get("OIDC_RP_CLIENT_ID", ""))
OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID", "")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET", "")
OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ.get("OIDC_OP_AUTHORIZATION_ENDPOINT", "")
OIDC_OP_TOKEN_ENDPOINT = os.environ.get("OIDC_OP_TOKEN_ENDPOINT", "")
OIDC_OP_USER_ENDPOINT = os.environ.get("OIDC_OP_USER_ENDPOINT", "")
OIDC_OP_JWKS_ENDPOINT = os.environ.get("OIDC_OP_JWKS_ENDPOINT", "")
OIDC_OP_LOGOUT_ENDPOINT = os.environ.get("OIDC_OP_LOGOUT_ENDPOINT", "")
OIDC_RP_SIGN_ALGO = os.environ.get("OIDC_RP_SIGN_ALGO", "RS256")
OIDC_RP_SCOPES = "openid email profile groups"
OIDC_ADMIN_GROUP = os.environ.get("OIDC_ADMIN_GROUP", "network-monitor-admins")
OIDC_VIEWER_GROUP = os.environ.get("OIDC_VIEWER_GROUP", "network-monitor-viewers")
OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = 900
OIDC_REDIRECT_ALLOWED_HOSTS = os.environ.get("OIDC_REDIRECT_ALLOWED_HOSTS", "").split(",")
OIDC_REDIRECT_URL = os.environ.get("OIDC_REDIRECT_URL", "")

# Se déconnecter termine aussi la session authentik : sans cela, le prochain « Se
# connecter » est servi par la session SSO restée ouverte. Voir apps/core/sso.py.
OIDC_OP_LOGOUT_URL_METHOD = "apps.core.sso.oidc_logout_url"

# Durée de conservation des résultats de checks.
MONITORING_RESULT_RETENTION_DAYS = int(os.environ.get("MONITORING_RESULT_RETENTION_DAYS", "30"))

# La liste des machines du lab, montée en lecture seule : elle reste la source de
# vérité, le routeur lisant le même fichier en busybox awk.
FLEET_INVENTORY = os.environ.get("FLEET_INVENTORY", "/app/inventory.conf")

# Le jeton que les machines envoient avec leur rapport horaire. Vide = tout POST est
# refusé : un secret non configuré ne doit jamais valoir « aucun secret requis ».
FLEET_REPORT_TOKEN = os.environ.get("REPORT_TOKEN", "")

# Deux passages horaires ratés, pas un seul.
FLEET_STALE_AFTER = int(os.environ.get("STALE_AFTER_SECONDS", "7800"))
FLEET_REPORT_RETENTION_DAYS = int(os.environ.get("FLEET_REPORT_RETENTION_DAYS", "90"))
FLEET_WUD_URL = os.environ.get("WUD_URL", "http://selene.argawaen.net:8082")

# Publier une approbation : un verbe sur un sujet que cette app écrit sans le lire.
# Aucune commande n'est jamais transmise -- voir apps/fleet/ntfy.py.
FLEET_NTFY_URL = os.environ.get("NTFY_URL", "http://selene.argawaen.net:8081")
FLEET_NTFY_TOPIC = os.environ.get("NTFY_WAKE_TOPIC", "homelab-wake")
FLEET_NTFY_TOKEN = os.environ.get("NTFY_TOKEN", "")

# Le code de la console journalise sur le logger "apps".
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"verbose": {"format": "{asctime} {levelname} {name} {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "verbose"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "apps": {"handlers": ["console"], "level": "INFO"},
        "celery": {"handlers": ["console"], "level": "INFO"},
    },
}
