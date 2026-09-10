from __future__ import annotations

import pytest
from django.test import Client


def test_liveness_envelope() -> None:
    client = Client()
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    assert body["data"]["service"] == "api"
    assert "request_id" in body["meta"]
    assert response["X-Request-ID"] == body["meta"]["request_id"]


def test_api_v1_health() -> None:
    client = Client()
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


@pytest.mark.django_db
def test_readiness_uses_control_plane_db() -> None:
    client = Client()
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ready"
    assert body["data"]["checks"]["database"] == "ok"
