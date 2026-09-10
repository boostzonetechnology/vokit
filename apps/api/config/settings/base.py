"""Shared Django settings. No tenant routing. Control-plane DB only."""

from __future__ import annotations

import os
from pathlib import Path

from shared_kernel.secrets import SecretRef

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name, default) or default).strip()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = _env(name, "1" if default else "0").lower()
    return raw in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = _env(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


SECRET_KEY_REF = SecretRef("DJANGO_SECRET_KEY")

DEBUG = False
ALLOWED_HOSTS = [
    part for part in _env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if part
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "control_plane.identity.apps.IdentityConfig",
    "control_plane.tenancy.apps.TenancyConfig",
    "control_plane.customers.apps.CustomersConfig",
    "control_plane.kyc.apps.KycConfig",
    "control_plane.billing.apps.BillingConfig",
    "control_plane.commission.apps.CommissionConfig",
    "control_plane.risk.apps.RiskConfig",
    "control_plane.agents.apps.AgentsConfig",
    "control_plane.telephony.apps.TelephonyConfig",
    "control_plane.recordings.apps.RecordingsConfig",
    "control_plane.integrations.apps.IntegrationsConfig",
    "control_plane.audit.apps.AuditConfig",
    "control_plane.notifications.apps.NotificationsConfig",
    "control_plane.platform_settings.apps.PlatformSettingsConfig",
    "control_plane.ops.apps.OpsConfig",
]

AUTH_USER_MODEL = "identity.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

MIDDLEWARE = [
    "shared_kernel.http.correlation.CorrelationIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "shared_kernel.http.request_log.RequestLogMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES: list[dict[str, object]] = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "EXCEPTION_HANDLER": "shared_kernel.http.exceptions.api_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
}

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    part for part in _env("CORS_ALLOWED_ORIGINS").split(",") if part
]

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "vokit_session"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)
CSRF_COOKIE_NAME = "vokit_csrf"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = _env_bool("CSRF_COOKIE_SECURE", False)
CSRF_FAILURE_VIEW = "shared_kernel.http.exceptions.csrf_failure"
CSRF_TRUSTED_ORIGINS = [part for part in _env("CSRF_TRUSTED_ORIGINS").split(",") if part]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "vokit-api",
    }
}

CELERY_BROKER_URL = _env("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = _env("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_TASK_ALWAYS_EAGER = _env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_IGNORE_RESULT = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

VOKIT_SERVICE_NAME = "api"
VOKIT_CURRENCY = "USD"

TENANT_RUNTIME = _env("TENANT_RUNTIME", "mysql")
TENANT_DB_HOST = _env("TENANT_DB_HOST", "127.0.0.1")
TENANT_DB_PORT = _env_int("TENANT_DB_PORT", 3306)
TENANT_DB_USER = _env("TENANT_DB_USER", "vokit")
TENANT_DB_PASSWORD_REF = _env("TENANT_DB_PASSWORD_REF", "TENANT_DB_PASSWORD")
TENANT_DB_NAME_A = _env("TENANT_DB_NAME_A", "vokit_tenant_a")
TENANT_DB_NAME_B = _env("TENANT_DB_NAME_B", "vokit_tenant_b")
TENANT_TLS_REQUIRED = _env_bool("TENANT_TLS_REQUIRED", False)
TENANT_POOL_MAX_PER_TENANT = _env_int("TENANT_POOL_MAX_PER_TENANT", 4)
TENANT_POOL_MAX_ACTIVE_TENANTS = _env_int("TENANT_POOL_MAX_ACTIVE_TENANTS", 16)
TENANT_CONNECT_TIMEOUT_SECONDS = _env_int("TENANT_CONNECT_TIMEOUT_SECONDS", 5)
TENANT_MIGRATION_CONCURRENCY = _env_int("TENANT_MIGRATION_CONCURRENCY", 2)
KYC_PROVIDER = _env("KYC_PROVIDER", "external")
KYC_API_KEY_REF = _env("KYC_API_KEY_REF", "KYC_API_KEY")
KYC_WEBHOOK_SECRET_REF = _env("KYC_WEBHOOK_SECRET_REF", "KYC_WEBHOOK_SECRET")
KYC_HOSTED_BASE_URL = _env("KYC_HOSTED_BASE_URL", "https://kyc.example.test")
KYC_ALLOW_HTTP_HOSTED = _env_bool("KYC_ALLOW_HTTP_HOSTED", False)
BILLING_STRIPE_WEBHOOK_SECRET_REF = _env(
    "BILLING_STRIPE_WEBHOOK_SECRET_REF", "STRIPE_WEBHOOK_SECRET"
)
BILLING_BRAINTREE_WEBHOOK_SECRET_REF = _env(
    "BILLING_BRAINTREE_WEBHOOK_SECRET_REF", "BRAINTREE_WEBHOOK_SECRET"
)
QDRANT_URL = _env("QDRANT_URL", "")
QDRANT_COLLECTION = _env("QDRANT_COLLECTION", "vokit_knowledge")
NUMBER_RESERVATION_SECONDS = _env_int("NUMBER_RESERVATION_SECONDS", 600)
VOKIT_INTERNAL_TELEPHONY_TOKEN = _env("VOKIT_INTERNAL_TELEPHONY_TOKEN", "")
VOKIT_INTERNAL_RECORDING_TOKEN = _env("VOKIT_INTERNAL_RECORDING_TOKEN", "")
RECORDING_ACCESS_TTL_SECONDS = _env_int("RECORDING_ACCESS_TTL_SECONDS", 60)
RECORDING_PUBLIC_BASE_URL = _env(
    "RECORDING_PUBLIC_BASE_URL", "https://recordings.vokit.test"
)
RECORDING_DEFAULT_RETENTION_DAYS = _env_int("RECORDING_DEFAULT_RETENTION_DAYS", 30)
INTEGRATION_ALLOW_HTTP = _env_bool("INTEGRATION_ALLOW_HTTP", False)
DEFAULT_FROM_EMAIL = _env("DEFAULT_FROM_EMAIL", "noreply@vokit.test")
SIP_EDGE_CONTROL_URL = _env("SIP_EDGE_CONTROL_URL", "")
VOICE_STT_PROVIDER = _env("VOICE_STT_PROVIDER", "")
VOICE_STT_API_KEY_REF = _env("VOICE_STT_API_KEY_REF", "VOICE_STT_API_KEY")
VOICE_TTS_PROVIDER = _env("VOICE_TTS_PROVIDER", "")
VOICE_TTS_API_KEY_REF = _env("VOICE_TTS_API_KEY_REF", "VOICE_TTS_API_KEY")
VOICE_LLM_PROVIDER = _env("VOICE_LLM_PROVIDER", "")
VOICE_LLM_API_KEY_REF = _env("VOICE_LLM_API_KEY_REF", "VOICE_LLM_API_KEY")
LIVE_FLAGS_ENABLED_BY_DEFAULT = _env_bool("LIVE_FLAGS_ENABLED_BY_DEFAULT", False)
VOKIT_PRODUCTION_HARDENING = False
BILLING_PROCESSOR_MODE = _env("BILLING_PROCESSOR_MODE", "sandbox")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "vokit_json": {
            "()": "shared_kernel.logging.StructuredJsonFormatter",
        }
    },
    "filters": {
        "correlation": {
            "()": "shared_kernel.http.correlation.CorrelationLogFilter",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "vokit_json",
            "filters": ["correlation"],
        }
    },
    "root": {
        "handlers": ["console"],
        "level": _env("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django.security": {"level": "WARNING", "propagate": True},
        "django.request": {"level": "WARNING", "propagate": True},
    },
}


def control_plane_database() -> dict[str, str | int]:
    return {
        "ENGINE": "django.db.backends.mysql",
        "NAME": _env("CONTROL_PLANE_DB_NAME", "vokit_control"),
        "USER": _env("CONTROL_PLANE_DB_USER", "vokit"),
        "PASSWORD": SecretRef("CONTROL_PLANE_DB_PASSWORD").resolve_optional(),
        "HOST": _env("CONTROL_PLANE_DB_HOST", "127.0.0.1"),
        "PORT": _env_int("CONTROL_PLANE_DB_PORT", 3306),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }


DATABASES = {"default": control_plane_database()}
