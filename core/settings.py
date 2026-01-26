import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost,api.alvelos.com,dev.alvelos.com,alvelos.com", cast=Csv())

# Para reverse proxy (NGINX/Cloudflare) identificar HTTPS corretamente
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True  # Usa X-Forwarded-Host para get_host()
USE_X_FORWARDED_PORT = True  # Opcional, se precisar de porta

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://dev.alvelos.com,https://alvelos.com",
    cast=Csv(),
)

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
    
    'authentication.apps.AuthenticationConfig',
    "user_profile",
    "services",
    "converter",
    'django_cleanup.apps.CleanupConfig',
]

NOTIFY_LOGIN_EMAIL = True

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
    "core.middleware.ApiExceptionLoggingMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
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

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = '/var/www/veloma-crm/static/'

MEDIA_URL = 'media/'
MEDIA_ROOT = '/var/www/veloma-crm/media/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# ====================== CORS CONFIGURAÇÃO (principal correção) ======================
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=False, cast=bool)  # Mantenha False em prod!

CORS_ALLOWED_ORIGINS = [
    "https://dev.alvelos.com",
    "https://alvelos.com",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://([a-z0-9-]+\.)?alvelos\.com$"
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",           # Para Bearer JWT
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_PREFLIGHT_MAX_AGE = 86400  # Cache preflight por 24h (bom para performance)

# Cookies cross-origin (crucial para subdomínios diferentes)
# SESSION_COOKIE_SAMESITE = 'None'
# SESSION_COOKIE_SECURE = True  # Deve ser True em HTTPS
# CSRF_COOKIE_SAMESITE = 'None'
# CSRF_COOKIE_SECURE = True

# ====================== REST FRAMEWORK ======================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # "EXCEPTION_HANDLER": "core.drf_exceptions.api_exception_handler",
}

# ====================== SPECTACULAR (Swagger/OpenAPI) ======================
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
        {"bearerAuth": []},
    ],

    "COMPONENT_SPLIT_REQUEST": True,
}

# ====================== OUTROS (mantidos ou ajustados) ======================
USER_PROFILE_ENCRYPTION_KEY = config("USER_PROFILE_ENCRYPTION_KEY", default="")

EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
EMAIL_TIMEOUT = config("EMAIL_TIMEOUT", default=30, cast=int)

PUBLIC_BASE_URL = config("PUBLIC_BASE_URL", default="https://api.alvelos.com")
FRONTEND_BASE_URL = config("FRONTEND_BASE_URL", default="https://dev.alvelos.com")
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