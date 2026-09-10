"""Production settings. Bind HTTP via gunicorn to 0.0.0.0:$PORT."""

from __future__ import annotations

from shared_kernel.secrets import SecretRef

from .base import *  # noqa: F403
from .base import (
    ALLOWED_HOSTS,
    CORS_ALLOWED_ORIGINS,
    CSRF_TRUSTED_ORIGINS,
    VOKIT_INTERNAL_RECORDING_TOKEN,
    VOKIT_INTERNAL_TELEPHONY_TOKEN,
    _env,
    _env_bool,
)
from .hardening import assert_production_boot

DEBUG = False
SECRET_KEY = SecretRef("DJANGO_SECRET_KEY").resolve()
LIVE_FLAGS_ENABLED_BY_DEFAULT = False
VOKIT_PRODUCTION_HARDENING = True
TENANT_RUNTIME = _env("TENANT_RUNTIME", "mysql")
TENANT_TLS_REQUIRED = _env_bool("TENANT_TLS_REQUIRED", True)

assert_production_boot(
    allowed_hosts=ALLOWED_HOSTS,
    telephony_token=VOKIT_INTERNAL_TELEPHONY_TOKEN,
    recording_token=VOKIT_INTERNAL_RECORDING_TOKEN,
    cors_origins=CORS_ALLOWED_ORIGINS,
    csrf_origins=CSRF_TRUSTED_ORIGINS,
    tenant_runtime=TENANT_RUNTIME,
    tenant_tls_required=TENANT_TLS_REQUIRED,
)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

PORT = _env("PORT", "8000")
