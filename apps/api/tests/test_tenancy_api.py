from __future__ import annotations

import json
import uuid

import pytest
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.tenancy.application.provision_tenant import ProvisionTenantCommand
from control_plane.tenancy.infrastructure.container import isolation_records, provisioner
from shared_kernel.ids import new_uuid7

PASSWORD = "Phase2-Demo!ok"


def _client() -> Client:
    return Client(enforce_csrf_checks=True)


def _csrf(client: Client) -> str:
    return client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]


def _post(client: Client, path: str, payload: dict):
    return client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=_csrf(client),
    )


def _user(
    email: str,
    principal: PrincipalType,
    role: str,
    tenant_id: uuid.UUID | None = None,
) -> User:
    user = User.objects.create_user(email=email, password=PASSWORD)
    DjangoMembershipRepository().create(
        MembershipRecord(
            id=new_uuid7(),
            user_id=user.id,
            principal_type=principal,
            role=role,
            tenant_id=tenant_id,
            customer_id=None,
            status=MembershipStatus.ACTIVE,
        )
    )
    return user


def _provision(name: str, database_name: str, tenant_id: uuid.UUID | None = None):
    return provisioner().execute(
        ProvisionTenantCommand(
            display_name=name,
            host="127.0.0.1",
            port=3306,
            name=database_name,
            db_username=f"u_{database_name}",
            db_password="TenantDbPass12!",
            tls_required=False,
            tenant_id=tenant_id,
        )
    )


@pytest.mark.django_db
def test_platform_can_provision_and_list_tenants() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    login = _post(
        client,
        "/api/v1/auth/login",
        {"email": "platform@vokit.test", "password": PASSWORD},
    )
    assert login.status_code == 200
    created = _post(
        client,
        "/api/v1/platform/tenants",
        {
            "display_name": "Agency A",
            "database": {
                "host": "127.0.0.1",
                "port": 3306,
                "name": "tenant_a_mem",
                "username": "u_tenant_a_mem",
                "password": "TenantDbPass12!",
                "tls_required": False,
            },
        },
    )
    assert created.status_code == 201
    assert created.json()["data"]["status"] == "ready"
    assert "password" not in json.dumps(created.json())
    listed = client.get("/api/v1/platform/tenants")
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1


@pytest.mark.django_db
def test_finance_admin_cannot_provision() -> None:
    _user("finance@vokit.test", PrincipalType.PLATFORM, "finance_admin")
    client = _client()
    _post(
        client,
        "/api/v1/auth/login",
        {"email": "finance@vokit.test", "password": PASSWORD},
    )
    response = _post(
        client,
        "/api/v1/platform/tenants",
        {
            "display_name": "Nope",
            "database": {
                "host": "127.0.0.1",
                "port": 3306,
                "name": "x",
                "username": "u_x",
                "password": "TenantDbPass12!",
            },
        },
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_agency_forged_tenant_id_cannot_switch_db() -> None:
    tenant_a = _provision("A", "iso_a")
    tenant_b = _provision("B", "iso_b")
    _user("agency-a@vokit.test", PrincipalType.AGENCY, "agency_owner", tenant_a.id)
    _user("agency-b@vokit.test", PrincipalType.AGENCY, "agency_owner", tenant_b.id)
    object_id = new_uuid7()
    isolation_records().put(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=tenant_b.id,
        claimed_tenant_id=None,
        permissions=frozenset(),
        object_id=object_id,
        payload="from-b",
    )
    client = _client()
    _post(
        client,
        "/api/v1/auth/login",
        {"email": "agency-a@vokit.test", "password": PASSWORD},
    )
    written = _post(
        client,
        "/api/v1/agency/data-plane/records",
        {"object_id": str(object_id), "payload": "from-a", "tenant_id": str(tenant_b.id)},
    )
    assert written.status_code == 201
    assert written.json()["data"]["tenant_id"] == str(tenant_a.id)
    assert written.json()["data"]["payload"] == "from-a"
    fetched = client.get(
        f"/api/v1/agency/data-plane/records/{object_id}?tenant_id={tenant_b.id}"
    )
    assert fetched.status_code == 200
    assert fetched.json()["data"]["payload"] == "from-a"

    other = _client()
    _post(
        other,
        "/api/v1/auth/login",
        {"email": "agency-b@vokit.test", "password": PASSWORD},
    )
    foreign = other.get(f"/api/v1/agency/data-plane/records/{object_id}")
    assert foreign.status_code == 200
    assert foreign.json()["data"]["payload"] == "from-b"


@pytest.mark.django_db
def test_missing_registry_mapping_denies_agency_record() -> None:
    missing = new_uuid7()
    _user("agency-missing@vokit.test", PrincipalType.AGENCY, "agency_owner", missing)
    client = _client()
    _post(
        client,
        "/api/v1/auth/login",
        {"email": "agency-missing@vokit.test", "password": PASSWORD},
    )
    response = _post(client, "/api/v1/agency/data-plane/records", {"payload": "x"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "tenant_route_denied"
