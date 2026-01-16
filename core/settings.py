from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://api.pdinfinita.app",
    cast=Csv(),
)

USE_X_FORWARDED_PROTO = config("USE_X_FORWARDED_PROTO", default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "drf_spectacular",
    "rest_framework",
    "corsheaders",

    "authentication",
    "user_profile",
    "services",
    "api",
    "app",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "services.middleware.session_touch.SessionTouchMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": config(
        "DATABASE_URL",
        default="sqlite:///db.sqlite3",
        cast=dj_database_url.parse,
    )
}

LANGUAGE_CODE = "pt-pt"
TIME_ZONE = "Europe/Lisbon"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

USER_PROFILE_ENCRYPTION_KEY = config("USER_PROFILE_ENCRYPTION_KEY", default="")

CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=False, cast=bool)
CORS_ALLOW_CREDENTIALS = config("CORS_ALLOW_CREDENTIALS", default=True, cast=bool)

EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
EMAIL_TIMEOUT = config("EMAIL_TIMEOUT", default=30, cast=int)

PUBLIC_BASE_URL = config("PUBLIC_BASE_URL", default="https://api.pdinfinita.app")
FRONTEND_BASE_URL = config("FRONTEND_BASE_URL", default="https://app.pdinfinita.app")
AUTH_RESET_PASSWORD_PATH = config("AUTH_RESET_PASSWORD_PATH", default="/reset-password")

REDIS_URL = config("REDIS_URL", default="redis://127.0.0.1:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLED = config("CELERY_ENABLED", default=True, cast=bool)

LOGIN_ALERT_ENABLED = config("LOGIN_ALERT_ENABLED", default=True, cast=bool)
LOGIN_ALERT_GEOLOOKUP_ENABLED = config("LOGIN_ALERT_GEOLOOKUP_ENABLED", default=True, cast=bool)
LOGIN_ALERT_GEOLOOKUP_URL = config("LOGIN_ALERT_GEOLOOKUP_URL", default="https://ipapi.co/{ip}/json/")
LOGIN_ALERT_GEOLOOKUP_TIMEOUT = config("LOGIN_ALERT_GEOLOOKUP_TIMEOUT", default=3, cast=int)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


SPECTACULAR_SETTINGS = {
    "TITLE": "Veloma CRM API",
    "DESCRIPTION": "API oficial da Veloma Contabilidade – Gestão de clientes, instituições e documentos.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,

    "CONTACT": {
        "name": "Veloma Contabilidade",
        "email": "suporte@velomacontabilidade.com",
    },

    "LICENSE": {
        "name": "Proprietary",
    },

    "SECURITY": [
        {
            "bearerAuth": [],
        }
    ],

    "COMPONENT_SPLIT_REQUEST": True,
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "authentication": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "services": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
