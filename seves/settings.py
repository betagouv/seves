"""
Django settings for seves project.

Generated by 'django-admin startproject' using Django 5.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path

import environ
import tempfile
import sentry_sdk
from django.core.exceptions import ImproperlyConfigured
from sentry_sdk.integrations.django import DjangoIntegration
from django.urls import reverse_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables (django-environ)
env = environ.Env(
    # set casting and default value
    DEBUG=(bool, False),
    DJANGO_ADMIN_ENABLED=(bool, False),
)
# Take environment variables from .env file
env.read_env(os.path.join(BASE_DIR, ".env"))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

# Django admin URL
ADMIN_ENABLED = env("DJANGO_ADMIN_ENABLED")
if ADMIN_ENABLED:
    ADMIN_URL = os.environ.get("DJANGO_ADMIN_URL")
    if not ADMIN_URL:
        raise ImproperlyConfigured("DJANGO_ADMIN_URL doit être défini dans les variables d'environnement")


# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "mozilla_django_oidc",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "sv.apps.SvConfig",
    "core.apps.CoreConfig",
    "account.apps.AccountConfig",
    "django_filters",
    "post_office",
    "reversion",
    "csp",
]
if ADMIN_ENABLED:
    INSTALLED_APPS.append("django.contrib.admin")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "seves.middlewares.LoginRequiredMiddleware",
    "reversion.middleware.RevisionMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "seves.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "seves.context_processors.select_empty_choice",
            ],
        },
    },
]

WSGI_APPLICATION = "seves.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": env.db(),
}

CACHES = {
    "default": {
        "BACKEND": env("CACHE_CLASS", default="django.core.cache.backends.locmem.LocMemCache"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "fr-fr"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_ROOT = "staticfiles"
STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Sentry
SENTRY_DSN = env("SENTRY_DSN", default=None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
    )


STORAGES = {
    "default": {"BACKEND": env("STORAGE_ENGINE")},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
AWS_S3_OBJECT_PARAMETERS = {
    "ContentDisposition": "attachment",
}


if all(
    [
        env("STORAGE_BUCKET_NAME", default=None),
        env("STORAGE_ACCESS_KEY", default=None),
        env("STORAGE_SECRET_KEY", default=None),
        env("STORAGE_URL", default=None),
    ]
):
    STORAGES["default"]["OPTIONS"] = {
        "bucket_name": env("STORAGE_BUCKET_NAME", default=None),
        "access_key": env("STORAGE_ACCESS_KEY", default=None),
        "secret_key": env("STORAGE_SECRET_KEY", default=None),
        "endpoint_url": env("STORAGE_URL", default=None),
        "file_overwrite": False,
    }
elif environ.Env(TEMP_STORAGE=(bool, False)):
    STORAGES["default"]["OPTIONS"] = {"location": tempfile.mkdtemp()}

AUTHENTICATION_BACKENDS = ("mozilla_django_oidc.auth.OIDCAuthenticationBackend",)
LOGIN_URL = reverse_lazy("login")
OIDC_RP_CLIENT_ID = env("OIDC_RP_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = env("OIDC_RP_CLIENT_SECRET")
OIDC_OP_AUTHORIZATION_ENDPOINT = env("OIDC_RP_AUTH_ENDPOINT")
OIDC_OP_TOKEN_ENDPOINT = env("OIDC_RP_TOKEN_ENDPOINT")
OIDC_OP_USER_ENDPOINT = env("OIDC_RP_USER_ENDPOINT")
OIDC_OP_JWKS_ENDPOINT = env("OIDC_RP_JWKS_ENDPOINT")
OIDC_RP_LOGOUT_ENDPOINT = env("OIDC_RP_LOGOUT_ENDPOINT")
OIDC_AUTHENTICATION_CALLBACK_URL = "custom_oidc_authentication_callback"
OIDC_OP_LOGOUT_URL_METHOD = "core.auth_views.logout"
OIDC_CALLBACK_CLASS = "core.auth_views.CustomOIDCAuthenticationCallbackView"
OIDC_CREATE_USER = False
LOGIN_REDIRECT_URL = "/"
OIDC_RP_SIGN_ALGO = "RS256"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]

POST_OFFICE = {
    "BACKENDS": {
        "default": env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"),
    },
    "DEFAULT_PRIORITY": env("EMAIL_PRIORITY", default="medium"),
    "MESSAGE_ID_ENABLED": True,
    "CELERY_ENABLED": True,
}

if env("EMAIL_HOST", default=None):
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_PORT = env("EMAIL_PORT")
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")


ROOT_URL = env("ROOT_URL", default=None)

SELECT_EMPTY_CHOICE = "Choisir dans la liste"

BYPASS_ANTIVIRUS = env("BYPASS_ANTIVIRUS", default=False)
CLAMAV_CONFIG_FILE = env("CLAMAV_CONFIG_FILE", default="/etc/clamav/clamd.conf")

CELERY_TASK_ALWAYS_EAGER = env("CELERY_TASK_ALWAYS_EAGER", default=False)
if not CELERY_TASK_ALWAYS_EAGER:
    CELERY_BROKER_URL = env.cache_url("SCALINGO_REDIS_URL")["LOCATION"]
    CELERY_REDIS_SOCKET_KEEPALIVE = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
    },
}

CAN_GIVE_ACCESS_GROUP = "access_admin"

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "cdn.jsdelivr.net")
CSP_FONT_SRC = ("'self'", "cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:")
CSP_CONNECT_SRC = ("'self'", "geo.api.gouv.fr")
SENTRY_ENV = env("SENTRY_ENVIRONMENT", default="demo")
SENTRY_REPORT_URL = env("SENTRY_REPORT_URL")
CSP_REPORT_URI = f"{SENTRY_REPORT_URL}&sentry_environment={SENTRY_ENV}"
