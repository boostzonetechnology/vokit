from __future__ import annotations

from django.conf import settings
from django.test import Client


def test_no_tenant_database_router() -> None:
    routers = getattr(settings, "DATABASE_ROUTERS", [])
    assert routers == []


def test_only_control_plane_default_alias() -> None:
    assert list(settings.DATABASES.keys()) == ["default"]


def test_internal_telephony_requires_service_token() -> None:
    client = Client()
    response = client.post("/internal/telephony/v1/voice-session/bootstrap/")
    assert response.status_code == 401


def test_internal_recording_requires_service_token() -> None:
    client = Client()
    response = client.post("/internal/recordings/v1/ingest/")
    assert response.status_code == 401
