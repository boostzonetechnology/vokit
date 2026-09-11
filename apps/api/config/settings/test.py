"""Deterministic tests. SQLite control plane + in-memory tenant runtime."""

from __future__ import annotations

import os

os.environ.setdefault("KYC_API_KEY", "test-kyc-key")
os.environ.setdefault("KYC_WEBHOOK_SECRET", "test-kyc-webhook")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "test-stripe-webhook")
os.environ.setdefault("BRAINTREE_WEBHOOK_SECRET", "test-braintree-webhook")

from .base import *  # noqa: F403

SECRET_KEY = "test-secret-not-for-production"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
TENANT_RUNTIME = "memory"
TENANT_TLS_REQUIRED = False
TENANT_DB_HOST = "127.0.0.1"
TENANT_DB_PORT = 3306
TENANT_DB_ADMIN_USER = "root"
TENANT_DB_ADMIN_PASSWORD_REF = "TENANT_DB_ADMIN_PASSWORD"
TENANT_DB_PASSWORD_REF = "TENANT_DB_PASSWORD"
KYC_ALLOW_HTTP_HOSTED = True
VOKIT_INTERNAL_TELEPHONY_TOKEN = "test-internal-telephony-token"
VOKIT_INTERNAL_RECORDING_TOKEN = "test-internal-recording-token"
INTEGRATION_ALLOW_HTTP = True
LIVE_FLAGS_ENABLED_BY_DEFAULT = True
VOKIT_PRODUCTION_HARDENING = False
BILLING_PROCESSOR_MODE = "sandbox"
