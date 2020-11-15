"""
Django's settings for multisite project.
"""
import platform
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = BASE_DIR.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '(qu$15^l4oqf9d+^-lb-ih#^i3xoh+vn=#sp)u)&k_fli*sd64'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

MyDomain = ".argawaen.net"
subdomains = ["www", "testsubject", "drone", "ayoaron"]

ALLOWED_HOSTS = ['127.0.0.1'] + [a + MyDomain for a in subdomains]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'markdownx',  # Allow support for Markdown datafiles.
    'common.apps.CommonConfig',
    'www.apps.WwwConfig',
    'connector.apps.ConnectorConfig',
    'drone.apps.DroneConfig',
    'ayoaron.apps.AyoaronConfig',
    'tsjt.apps.TsjtConfig',
    'www_meteo.apps.WwwmeteoConfig',
    'www_netadmin.apps.WwwnetadminConfig',
]

MIDDLEWARE = [
    'multisite.vhosts.VHostMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'multisite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            SITE_DIR / 'data' / 'templates' / 'common',
            SITE_DIR / 'data' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'multisite.wsgi.application'

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
if platform.system() == "Windows":
    EMAIL_HOST = "192.168.23.1"
else:
    EMAIL_HOST = "127.0.0.1"
EMAIL_PORT = "587"
EMAIL_HOST_USER = "site@argawaen.net"
EMAIL_HOST_PASSWORD = "site"
EMAIL_USE_TLS = True

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'Site_Common',
            'USER': 'www_common',
            'PASSWORD': 'Melissa1',
            'HOST': '192.168.23.1',
            'PORT': '3306',
            'OPTIONS': {'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"},
            'TEST': {
                'NAME': 'Site_Common_test',
            }
        },
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'CET'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

# Les static
STATIC_URL = '/static/'
STATICFILES_DIRS = [SITE_DIR / 'data' / 'static']

# Les medias
MEDIA_URL = "/media/"
MEDIA_ROOT = SITE_DIR / 'data' / 'media'
print(MEDIA_ROOT)

# Login redirection
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Markdownx configuration
# https://neutronx.github.io/django-markdownx/
MARKDOWNX_MARKDOWN_EXTENSIONS = [
    'markdown.extensions.extra',
    'markdown.extensions.codehilite',
]
