"""Phase D: least-privilege on residual require_principal endpoints."""

from __future__ import annotations

import json
import uuid

import pytest
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
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


def _create_user(
    email: str,
    *,
    principal: PrincipalType,
    role: str,
    tenant_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
) -> User:
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
    response = _post(
        client, "/api/v1/auth/login", {"email": email, "password": PASSWORD}
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_support_admin_cannot_list_or_create_platform_invitations() -> None:
    _create_user("support-lp@vokit.test", principal=PrincipalType.PLATFORM, role="support_admin")
    client = _client()
    _login(client, "support-lp@vokit.test")
    listed = client.get("/api/v1/platform/invitations")
    assert listed.status_code == 403
    created = _post(
        client,
        "/api/v1/platform/invitations",
        {"email": "x@vokit.test", "principal_type": "platform", "role": "support_admin"},
    )
    assert created.status_code == 403


@pytest.mark.django_db
def test_support_admin_cannot_disable_users() -> None:
    _create_user("support-dis@vokit.test", principal=PrincipalType.PLATFORM, role="support_admin")
    target = _create_user(
        "target-dis@vokit.test", principal=PrincipalType.PLATFORM, role="support_admin"
    )
    client = _client()
    _login(client, "support-dis@vokit.test")
    denied = _post(client, f"/api/v1/platform/users/{target.id}/disable", {})
    assert denied.status_code == 403


@pytest.mark.django_db
def test_finance_admin_dashboard_still_allowed_via_billing_view() -> None:
    _create_user("fin-dash@vokit.test", principal=PrincipalType.PLATFORM, role="finance_admin")
    client = _client()
    _login(client, "fin-dash@vokit.test")
    response = client.get("/api/v1/platform/dashboard")
    assert response.status_code == 200


@pytest.mark.django_db
def test_agency_finance_cannot_start_kyc_but_owner_can() -> None:
    from tests.tenant_db_fixtures import tenant_db_payload

    _create_user("sa-kyc-lp@vokit.test", principal=PrincipalType.PLATFORM, role="super_admin")
    platform = _client()
    _login(platform, "sa-kyc-lp@vokit.test")
    created = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "KYC LP",
            "legal_name": "KYC LP",
            "owner_email": "owner-kyc-lp@vokit.test",
            "database": tenant_db_payload("owner-kyc-lp@vokit.test"),
        },
    )
    assert created.status_code == 201
    agency_id = created.json()["data"]["id"]
    activated = _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate", "confirm": True},
    )
    assert activated.status_code == 200

    _create_user(
        "fin-kyc-lp@vokit.test",
        principal=PrincipalType.AGENCY,
        role="agency_finance",
        tenant_id=uuid.UUID(agency_id),
    )
    _create_user(
        "owner-kyc-lp2@vokit.test",
        principal=PrincipalType.AGENCY,
        role="agency_owner",
        tenant_id=uuid.UUID(agency_id),
    )

    finance = _client()
    _login(finance, "fin-kyc-lp@vokit.test")
    assert finance.get("/api/v1/agency/kyc").status_code == 403
    assert _post(finance, "/api/v1/agency/kyc/session", {}).status_code == 403

    owner = _client()
    _login(owner, "owner-kyc-lp2@vokit.test")
    assert owner.get("/api/v1/agency/kyc").status_code == 200
    session = _post(owner, "/api/v1/agency/kyc/session", {})
    assert session.status_code == 201
