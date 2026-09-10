from __future__ import annotations

from django.test import Client


def test_accepts_valid_inbound_request_id() -> None:
    client = Client()
    inbound = "11111111-1111-4111-8111-111111111111"
    response = client.get("/health", HTTP_X_REQUEST_ID=inbound)
    assert response["X-Request-ID"] == inbound
    assert response.json()["meta"]["request_id"] == inbound


def test_ignores_forged_non_uuid_request_id() -> None:
    client = Client()
    response = client.get("/health", HTTP_X_REQUEST_ID="tenant-B-please")
    assert response["X-Request-ID"] != "tenant-B-please"
    assert response.json()["meta"]["request_id"] == response["X-Request-ID"]
