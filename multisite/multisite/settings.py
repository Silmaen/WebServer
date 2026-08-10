"""
Django's settings for multisite project.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = BASE_DIR.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '(qu$15^l4oqf9d+^-lb-ih#^i3xoh+vn=#sp)u)&k_fli*sd64')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS',
    '127.0.0.1,localhost,www.argawaen.net'
).split(',')

CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS',
    'http://127.0.0.1:8000,http://localhost:8000,https://www.argawaen.net'
).split(',')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.forms',
    'markdownx',  # Allow support for Markdown datafiles.
    # Third party, for the console (apps.* below)
    'rest_framework',
    'django_filters',
    'django_htmx',
    'django_celery_beat',
    'mozilla_django_oidc',
    'common.apps.CommonConfig',
    'www.apps.WwwConfig',
    'connector.apps.ConnectorConfig',
    # The homelab console and the network monitoring, moved here from their own
    # repositories -- see _ops/docs/console-merge.md in home-server-stacks. They keep
    # the `apps.` prefix on purpose: it preserves every dotted path inside the moved
    # code and, more importantly, the migration app_labels, so the existing database
    # transfers instead of being rebuilt.
    'apps.core',
    'apps.network',
    'apps.devices',
    'apps.monitoring',
    'apps.dashboard',
    'apps.fleet',
    'apps.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'mozilla_django_oidc.middleware.SessionRefresh',
    'apps.core.middleware.InactiveUserMiddleware',
]

ROOT_URLCONF = 'multisite.urls'

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            SITE_DIR / 'data' / 'templates' / 'common',
            # The console's own root. Its templates reference each other bare
            # ("base.html", "fleet/index.html", "includes/navbar.html"), and none of
            # those names exist under www/ or common/ -- so they resolve here and
            # needed no rewriting when they moved.
            SITE_DIR / 'data' / 'templates' / 'console',
            SITE_DIR / 'data' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'www.context_processors.navigation',
            ],
        },
    },
]

WSGI_APPLICATION = 'multisite.wsgi.application'

# Proxy — Django est derrière nginx
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

EMAIL_HOST = os.environ.get('EMAIL_HOST', '127.0.0.1')
EMAIL_PORT = os.environ.get('EMAIL_PORT', '587')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'site@argawaen.net')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'site')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')

# Email
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'webmaster@argawaen.net')

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'argawaen'),
        'USER': os.environ.get('DB_USER', 'argawaen'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'argawaen'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    },
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# Les static
STATIC_URL = '/static/'
STATICFILES_DIRS = [SITE_DIR / 'data' / 'static']
STATIC_ROOT = SITE_DIR / 'staticfiles'

# Les medias
MEDIA_URL = "/media/"
MEDIA_ROOT = SITE_DIR / 'data' / 'media'

# Login redirection
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Markdownx configuration
# https://neutronx.github.io/django-markdownx/
MARKDOWNX_MARKDOWN_EXTENSIONS = [
    'markdown.extensions.extra',
    'markdown.extensions.codehilite',
    'pymdownx.tasklist',
]
MARKDOWNX_MARKDOWN_EXTENSION_CONFIGS = {
    'markdown.extensions.codehilite': {
        'css_class': 'codehilite',
        'guess_lang': True,
    },
    'pymdownx.tasklist': {
        'custom_checkbox': True,
    },
}

# Celery
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_ROUTES = {
    # The scanner worker owns these: they need host networking and NET_RAW.
    "apps.network.*": {"queue": "network"},
    "apps.devices.tasks.*": {"queue": "network"},
}
CELERY_BEAT_SCHEDULE = {
    # --- the console, moved from network_monitor ---------------------------
    # `maintenance` is a queue of its own, consumed alongside `celery`: a purge that
    # shares a queue with the check firehose never gets a turn. That starved
    # cleanup_old_results for months and let the results table reach 1.9 M rows.
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
    # --- www's own, older monitoring --------------------------------------
    # These overlap with apps.monitoring above and are a third check engine in the
    # lab, after gatus and that one. Reconciling them is the point of having a single
    # repository; until then they run side by side.
    "verifier-machines": {
        "task": "www.tasks.verifier_machines",
        "schedule": 300.0,
    },
    "verifier-serveurs": {
        "task": "www.tasks.verifier_serveurs",
        "schedule": 300.0,
    },
}

# Monitoring
MONITORING_DOMAINE_DEFAUT = os.environ.get("MONITORING_DOMAINE_DEFAUT", "")


# ===========================================================================
# The homelab console, moved here from network_monitor (its own repository until
# now) -- see _ops/docs/console-merge.md in home-server-stacks for the whole story.
# ===========================================================================

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

# The site is deliberately public -- a CV and some projects -- so authentik cannot
# gate the vhost: that would gate those too. It is OIDC *inside* Django, with the
# console views requiring a session and the local ModelBackend kept as the fallback
# for the day authentik itself is down.
AUTHENTICATION_BACKENDS = [
    "apps.core.auth.OIDCAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# The existing login page of the site, by url name -- not the one network_monitor
# shipped. One site, one login.
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

# How long per-device check results are kept.
MONITORING_RESULT_RETENTION_DAYS = int(os.environ.get("MONITORING_RESULT_RETENTION_DAYS", "30"))

# The lab's machine list, mounted read-only from the home-server-stacks checkout. It
# stays the source of truth -- busybox awk on the router parses the same file.
FLEET_INVENTORY = os.environ.get("FLEET_INVENTORY", "/app/inventory.conf")

# The bearer token the machines send with their hourly report. Empty means every POST
# is refused: an unset secret must never read as "no secret required".
FLEET_REPORT_TOKEN = os.environ.get("REPORT_TOKEN", "")

# Two missed hourly runs, not one.
FLEET_STALE_AFTER = int(os.environ.get("STALE_AFTER_SECONDS", "7800"))
FLEET_REPORT_RETENTION_DAYS = int(os.environ.get("FLEET_REPORT_RETENTION_DAYS", "90"))
FLEET_WUD_URL = os.environ.get("WUD_URL", "http://selene.argawaen.net:8082")

# Publishing an approval: a verb on a topic this app can write and not read. No
# command is ever transmitted -- see apps/fleet/ntfy.py.
FLEET_NTFY_URL = os.environ.get("NTFY_URL", "http://selene.argawaen.net:8081")
FLEET_NTFY_TOPIC = os.environ.get("NTFY_WAKE_TOPIC", "homelab-wake")
FLEET_NTFY_TOKEN = os.environ.get("NTFY_TOKEN", "")

# The moved code logs to the "apps" logger.
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
