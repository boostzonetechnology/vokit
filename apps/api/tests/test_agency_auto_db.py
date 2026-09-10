from __future__ import annotations

import uuid

import pytest
from django.test import Client, override_settings

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.tenancy.application.allocate_database import tenant_database_name
from control_plane.tenancy.infrastructure.container import database_repo
from shared_kernel.ids import new_uuid7

PASSWORD = "Phase2-Demo!ok"


def _client() -> Client:
    return Client(enforce_csrf_checks=True)


def _csrf(client: Client) -> str:
    return client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]


def _post(client: Client, path: str, payload: dict):
    import json

    return client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=_csrf(client),
    )


def _platform() -> User:
    user = User.objects.create_user(email="platform-auto-db@vokit.test", password=PASSWORD)
    DjangoMembershipRepository().create(
        MembershipRecord(
            id=new_uuid7(),
            user_id=user.id,
            principal_type=PrincipalType.PLATFORM,
            role="super_admin",
            tenant_id=None,
            customer_id=None,
            status=MembershipStatus.ACTIVE,
        )
    )
    return user


@pytest.mark.django_db
@override_settings(
    TENANT_RUNTIME="memory",
    TENANT_DB_HOST="127.0.0.1",
    TENANT_DB_PORT=3306,
    TENANT_DB_PASSWORD_REF="TENANT_DB_PASSWORD",
    TENANT_TLS_REQUIRED=False,
)
def test_agency_create_allocates_distinct_databases() -> None:
    _platform()
    client = _client()
    assert _post(
        client,
        "/api/v1/auth/login",
        {"email": "platform-auto-db@vokit.test", "password": PASSWORD},
    ).status_code == 200
    first = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Agency One",
            "legal_name": "Agency One LLC",
            "owner_email": "owner1@example.test",
            "commission_rate_bps": 1000,
        },
    )
    second = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Agency Two",
            "legal_name": "Agency Two LLC",
            "owner_email": "owner2@example.test",
            "commission_rate_bps": 1100,
        },
    )
    assert first.status_code == 201
    assert second.status_code == 201
    body = first.json()
    assert "password" not in str(body).lower()
    assert "secret_ref" not in str(body.get("data", {}))
    tid1 = uuid.UUID(first.json()["data"]["id"])
    tid2 = uuid.UUID(second.json()["data"]["id"])
    db1 = database_repo().get_for_tenant(tid1)
    db2 = database_repo().get_for_tenant(tid2)
    assert db1 is not None and db2 is not None
    assert db1.name == tenant_database_name(tid1)
    assert db2.name == tenant_database_name(tid2)
    assert db1.name != db2.name
    assert db1.host == "127.0.0.1"
    assert db1.secret_ref == "TENANT_DB_PASSWORD"


@pytest.mark.django_db
@override_settings(
    TENANT_RUNTIME="memory",
    TENANT_DB_HOST="127.0.0.1",
    TENANT_DB_PORT=3306,
    TENANT_DB_PASSWORD_REF="TENANT_DB_PASSWORD",
)
def test_agency_create_rejects_client_database_block() -> None:
    _platform()
    client = _client()
    _post(
        client,
        "/api/v1/auth/login",
        {"email": "platform-auto-db@vokit.test", "password": PASSWORD},
    )
    response = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Forged",
            "legal_name": "Forged",
            "owner_email": "forged@example.test",
            "database": {
                "host": "evil.example",
                "port": 9999,
                "name": "stolen",
                "secret_ref": "OTHER",
                "tls_required": True,
            },
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
