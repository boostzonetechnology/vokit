from __future__ import annotations

import json
import uuid

import pytest
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.rbac_seed import ensure_rbac_seeded
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import Permission, Role, RolePermission, User
from shared_kernel.ids import new_uuid7

PASSWORD = "Phase2-Demo!ok"


def _client() -> Client:
    return Client(enforce_csrf_checks=True)


def _csrf(client: Client) -> str:
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 200
    return response.json()["data"]["csrf_token"]


def _post(client: Client, path: str, payload: dict, csrf: str | None = None):
    token = csrf or _csrf(client)
    return client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )


def _patch(client: Client, path: str, payload: dict, csrf: str | None = None):
    token = csrf or _csrf(client)
    return client.patch(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )


def _create_user(
    email: str,
    *,
    principal: PrincipalType,
    role: str,
    tenant_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
) -> User:
    ensure_rbac_seeded()
    user = User.objects.create_user(email=email, password=PASSWORD)
    DjangoMembershipRepository().create(
        MembershipRecord(
            id=new_uuid7(),
            user_id=user.id,
            principal_type=principal,
            role=role,
            tenant_id=tenant_id,
            customer_id=customer_id,
            status=MembershipStatus.ACTIVE,
        )
    )
    return user


def _login(client: Client, email: str) -> None:
    response = _post(client, "/api/v1/auth/login", {"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.content


@pytest.mark.django_db
def test_super_admin_bypasses_without_pivot_and_lists_roles() -> None:
    _create_user("sa@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    client = _client()
    _login(client, "sa@vokit.test")
    session = client.get("/api/v1/auth/session")
    body = session.json()["data"]
    assert body["is_super_admin"] is True
    assert body["permissions"] == []
    roles = client.get("/api/v1/platform/roles")
    assert roles.status_code == 200
    assert any(row["slug"] == "super_admin" for row in roles.json()["data"])


@pytest.mark.django_db
def test_finance_admin_denied_without_role_view() -> None:
    _create_user("fin@vokit.test", principal=PrincipalType.PLATFORM, role="finance_admin")
    client = _client()
    _login(client, "fin@vokit.test")
    denied = client.get("/api/v1/platform/roles")
    assert denied.status_code == 403


@pytest.mark.django_db
def test_sync_is_additive() -> None:
    _create_user("sa2@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    ensure_rbac_seeded()
    before = Permission.objects.count()
    Permission.objects.create(
        id=new_uuid7(),
        namespace="platform",
        code="custom.demo",
        description="keep me",
        is_custom=True,
    )
    client = _client()
    _login(client, "sa2@vokit.test")
    synced = _post(client, "/api/v1/platform/permissions/sync", {})
    assert synced.status_code == 200
    assert Permission.objects.filter(code="custom.demo").exists()
    assert Permission.objects.count() >= before + 1


@pytest.mark.django_db
def test_cannot_attach_platform_perm_to_agency_role_via_patch() -> None:
    _create_user("sa3@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    agency_role = Role.objects.get(slug="agency_finance")
    client = _client()
    _login(client, "sa3@vokit.test")
    response = _patch(
        client,
        f"/api/v1/platform/roles/{agency_role.id}",
        {"permissions": ["payout.approve"]},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.django_db
def test_agency_role_list_requires_team_view() -> None:
    tenant = uuid.uuid4()
    _create_user(
        "af@vokit.test",
        principal=PrincipalType.AGENCY,
        role="agency_finance",
        tenant_id=tenant,
    )
    client = _client()
    _login(client, "af@vokit.test")
    denied = client.get("/api/v1/agency/roles")
    assert denied.status_code == 403

    _create_user(
        "ao@vokit.test",
        principal=PrincipalType.AGENCY,
        role="agency_owner",
        tenant_id=uuid.uuid4(),
    )
    client2 = _client()
    _login(client2, "ao@vokit.test")
    ok = client2.get("/api/v1/agency/roles")
    assert ok.status_code == 200
    assert any(row["slug"] == "agency_owner" for row in ok.json()["data"])


@pytest.mark.django_db
def test_cannot_delete_system_role() -> None:
    _create_user("sa4@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    role = Role.objects.get(slug="finance_admin")
    client = _client()
    _login(client, "sa4@vokit.test")
    csrf = _csrf(client)
    deleted = client.delete(
        f"/api/v1/platform/roles/{role.id}",
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert deleted.status_code == 403


@pytest.mark.django_db
def test_create_custom_platform_role_and_use_permission() -> None:
    _create_user("sa5@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    client = _client()
    _login(client, "sa5@vokit.test")
    created = _post(
        client,
        "/api/v1/platform/roles",
        {
            "slug": "billing_viewer",
            "display_name": "Billing Viewer",
            "namespace": "platform",
            "permissions": ["billing.view", "role.view"],
        },
    )
    assert created.status_code == 201
    assert created.json()["data"]["is_system"] is False
    assert "billing.view" in created.json()["data"]["permissions"]
