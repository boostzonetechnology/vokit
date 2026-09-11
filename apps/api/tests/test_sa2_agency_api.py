from __future__ import annotations

import json
import uuid

import pytest
from django.core import mail
from django.test import Client

from control_plane.audit.models import AuditEvent
from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.notifications.models import NotificationDelivery
from shared_kernel.ids import new_uuid7
from tests.tenant_db_fixtures import tenant_db_payload

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
    login = _post(
        client,
        "/api/v1/auth/login",
        {"email": email, "password": PASSWORD},
    )
    assert login.status_code == 200


@pytest.mark.django_db
def test_agency_create_is_invited_and_delivers_email() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    mail.outbox.clear()
    response = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Invite Co",
            "legal_name": "Invite Co LLC",
            "owner_email": "owner-invite@vokit.test",
            "database": tenant_db_payload("owner-invite@vokit.test"),
            "commission_rate_bps": 1000,
        },
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["status"] == "invited"
    assert "owner_invitation_token" not in body
    assert NotificationDelivery.objects.filter(
        event_type="invitation.agency", recipient_email="owner-invite@vokit.test"
    ).exists()
    assert len(mail.outbox) >= 1


@pytest.mark.django_db
def test_agency_create_owner_conflict() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    _user("taken@vokit.test", PrincipalType.PLATFORM, "support_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    response = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Conflict Co",
            "legal_name": "Conflict Co",
            "owner_email": "taken@vokit.test",
            "database": tenant_db_payload("taken@vokit.test"),
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "owner_conflict"


@pytest.mark.django_db
def test_platform_can_change_commission_rate() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    created = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Rate Co",
            "legal_name": "Rate Co",
            "owner_email": "rate-owner@vokit.test",
            "database": tenant_db_payload("rate-owner@vokit.test"),
            "commission_rate_bps": 500,
        },
    )
    agency_id = created.json()["data"]["id"]
    changed = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/commission",
        {"commission_rate_bps": 2500},
    )
    assert changed.status_code == 200
    assert changed.json()["data"]["commission_rate_bps"] == 2500
    assert AuditEvent.objects.filter(
        action="agency.commission.changed", entity_id=agency_id
    ).exists()


@pytest.mark.django_db
def test_status_restrict_and_review_apply_default_gates() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    created = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Gate Co",
            "legal_name": "Gate Co",
            "owner_email": "gate-owner@vokit.test",
            "database": tenant_db_payload("gate-owner@vokit.test"),
        },
    )
    agency_id = created.json()["data"]["id"]
    _post(client, f"/api/v1/platform/agencies/{agency_id}/status", {"action": "activate"})
    restricted = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "restrict", "reason": "manual review"},
    )
    assert restricted.status_code == 200
    caps = restricted.json()["data"]["capabilities"]
    assert caps["create_customers"] is False
    assert caps["request_payouts"] is False
    assert AuditEvent.objects.filter(
        action="agency.status.changed", entity_id=agency_id
    ).exists()
    _post(client, f"/api/v1/platform/agencies/{agency_id}/status", {"action": "activate"})
    reviewed = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "review"},
    )
    assert reviewed.json()["data"]["capabilities"]["request_payouts"] is False


@pytest.mark.django_db
def test_partial_capabilities_preserve_untouched_flags() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    created = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Caps Co",
            "legal_name": "Caps Co",
            "owner_email": "caps-owner@vokit.test",
            "database": tenant_db_payload("caps-owner@vokit.test"),
            "capabilities": {
                "create_customers": True,
                "create_agents": False,
                "purchase_numbers": True,
                "request_payouts": True,
                "existing_customer_services": True,
            },
        },
    )
    agency_id = created.json()["data"]["id"]
    patched = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/capabilities",
        {"capabilities": {"create_customers": False}},
    )
    assert patched.status_code == 200
    caps = patched.json()["data"]["capabilities"]
    assert caps["create_customers"] is False
    assert caps["create_agents"] is False
    assert caps["purchase_numbers"] is True


@pytest.mark.django_db
def test_create_agents_capability_blocks_agency_actor() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    created = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Agent Gate",
            "legal_name": "Agent Gate",
            "owner_email": "agent-gate@vokit.test",
            "database": tenant_db_payload("agent-gate@vokit.test"),
        },
    )
    agency_id = created.json()["data"]["id"]
    _post(platform, f"/api/v1/platform/agencies/{agency_id}/status", {"action": "activate"})
    _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/capabilities",
        {"capabilities": {"create_agents": False}},
    )
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Cust", "agency_id": agency_id},
    )
    customer_id = customer.json()["data"]["id"]
    _user(
        "agency-gate@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        uuid.UUID(agency_id),
    )
    agency = _client()
    _login(agency, "agency-gate@vokit.test")
    denied = _post(
        agency,
        "/api/v1/agency/agents",
        {"display_name": "Blocked", "customer_id": customer_id},
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "agency_cannot_create_agent"
    privileged = _post(
        platform,
        "/api/v1/platform/agents",
        {"display_name": "Allowed", "customer_id": customer_id},
    )
    assert privileged.status_code == 201


@pytest.mark.django_db
def test_agency_finance_and_notes_endpoints() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    created = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Finance Co",
            "legal_name": "Finance Co",
            "owner_email": "finance-owner@vokit.test",
            "database": tenant_db_payload("finance-owner@vokit.test"),
        },
    )
    agency_id = created.json()["data"]["id"]
    finance = client.get(f"/api/v1/platform/agencies/{agency_id}/finance")
    assert finance.status_code == 200
    data = finance.json()["data"]
    assert data["agency_id"] == agency_id
    assert "buckets" in data
    assert "payouts" in data
    note = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/notes",
        {"body": "Watch payout risk", "risk_flag": True},
    )
    assert note.status_code == 201
    assert note.json()["data"]["risk_flag"] is True
    listed = client.get(f"/api/v1/platform/agencies/{agency_id}/notes")
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1


@pytest.mark.django_db
def test_agency_list_filters_and_team_by_agency() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    first = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Alpha Filter",
            "legal_name": "Alpha Filter",
            "owner_email": "alpha-filter@vokit.test",
            "database": tenant_db_payload("alpha-filter@vokit.test"),
        },
    )
    agency_id = first.json()["data"]["id"]
    listed = client.get("/api/v1/platform/agencies?status=invited&name=alpha")
    assert listed.status_code == 200
    assert any(row["id"] == agency_id for row in listed.json()["data"])
    _user(
        "agency-member@vokit.test",
        PrincipalType.AGENCY,
        "agency_admin",
        uuid.UUID(agency_id),
    )
    team = client.get(f"/api/v1/platform/users?agency_id={agency_id}")
    assert team.status_code == 200
    emails = {row["email"] for row in team.json()["data"]}
    assert "agency-member@vokit.test" in emails
