"""Environment for the Pipecat voice peer (no Django provider SoT)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PACKAGE_DIR = Path(__file__).resolve().parent
_SERVICE_ROOT = _PACKAGE_DIR.parent.parent
_REPO_ROOT = _SERVICE_ROOT.parent.parent
load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_SERVICE_ROOT / ".env")
load_dotenv(_SERVICE_ROOT / ".env.example", override=False)


def _env(key: str, default: str = "") -> str:
    return (os.environ.get(key, default) or default).strip()


def _env_int(key: str, default: int) -> int:
    raw = _env(key, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _env_list(key: str) -> list[str]:
    raw = _env(key)
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


@dataclass(frozen=True)
class PipecatVoiceConfig:
    media_ws_token: str
    django_internal_base_url: str
    internal_telephony_token: str
    host: str
    port: int
    heartbeat_seconds: float
    inbound_diag: bool = False
    allowed_origins: tuple[str, ...] = ()
    sample_rate: int = 8000
    ulaw_frame_bytes: int = 160
    qdrant_url: str = ""

    @property
    def django_base(self) -> str:
        return self.django_internal_base_url.rstrip("/")


def load_config() -> PipecatVoiceConfig:
    return PipecatVoiceConfig(
        media_ws_token=_env("VOKIT_MEDIA_WS_TOKEN"),
        django_internal_base_url=_env(
            "DJANGO_INTERNAL_BASE_URL",
            "http://127.0.0.1:8000",
        ),
        internal_telephony_token=_env("VOKIT_INTERNAL_TELEPHONY_TOKEN"),
        host=_env("PIPECAT_HOST", "0.0.0.0"),
        port=_env_int("PIPECAT_PORT", 8100),
        heartbeat_seconds=float(_env("PIPECAT_HEARTBEAT_SECONDS", "2") or "2"),
        inbound_diag=_env("PIPECAT_INBOUND_DIAG", "0").lower() in {"1", "true", "yes"},
        allowed_origins=tuple(_env_list("PIPECAT_ALLOWED_ORIGINS")),
        qdrant_url=_env("QDRANT_URL"),
    )
