"""Local development. Control-plane MySQL only — no tenant router."""

from __future__ import annotations

import os
from pathlib import Path

from shared_kernel.secrets import SecretRef


def _load_dotenv() -> None:
    path = Path(__file__).resolve().parent.parent.parent / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

from .base import *  # noqa: E402, F403
from .base import CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS, _env, _env_bool  # noqa: E402

os.environ.setdefault("DJANGO_SECRET_KEY", "local-dev-only-not-for-production")

SECRET_KEY = SecretRef("DJANGO_SECRET_KEY").resolve()
DEBUG = _env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [
    part
    for part in _env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")
    if part
]
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CELERY_TASK_ALWAYS_EAGER = _env_bool("CELERY_TASK_ALWAYS_EAGER", True)

_local_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
]
CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS or _local_origins
CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS or _local_origins
LIVE_FLAGS_ENABLED_BY_DEFAULT = _env_bool("LIVE_FLAGS_ENABLED_BY_DEFAULT", True)
