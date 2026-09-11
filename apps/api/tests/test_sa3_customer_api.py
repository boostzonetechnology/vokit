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
from tests.tenant_db_fixtures import platform_customer_body, tenant_db_payload

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
    login = _post(client, "/api/v1/auth/login", {"email": email, "password": PASSWORD})
    assert login.status_code == 200


def _create_agency(client: Client, name: str, owner: str):
    response = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": name,
            "legal_name": name,
            "owner_email": owner,
            "database": tenant_db_payload(owner),
        },
    )
    assert response.status_code == 201
    agency_id = response.json()["data"]["id"]
    activated = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate"},
    )
    assert activated.status_code == 200
    return activated.json()["data"]


@pytest.mark.django_db
def test_create_customer_requires_owner_email_and_starts_invited() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "SA3 A", "oa-sa3a@vokit.test")
    missing = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "No Email", "agency_id": agency["id"]},
    )
    assert missing.status_code == 400
    owner_email = "owner-sa3@vokit.test"
    created = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(
            agency["id"],
            "Invited Co",
            owner_email=owner_email,
            legal_name="Invited Legal",
            phone="+15551212",
            country="US",
            timezone="America/New_York",
        ),
    )
    assert created.status_code == 201
    body = created.json()["data"]
    assert body["status"] == "invited"
    assert body["owner_email"] == owner_email
    assert body["legal_name"] == "Invited Legal"
    assert "owner_invitation_token" not in json.dumps(created.json())
    from control_plane.identity.models import Invitation

    assert Invitation.objects.filter(email=owner_email).exists()


@pytest.mark.django_db
def test_accept_invitation_activates_customer(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def _capture_deliver(**kwargs):
        captured["token"] = kwargs["token"]
        from control_plane.audit.application.record import RecordAuditCommand
        from control_plane.audit.infrastructure.container import record_audit

        record_audit().execute(
            RecordAuditCommand(
                action="role.invited",
                entity_type="invitation",
                entity_id=kwargs["email"],
                actor_id=kwargs["actor_id"],
                actor_role=kwargs["actor_role"],
                tenant_id=kwargs["tenant_id"],
                customer_id=kwargs["customer_id"],
                after_summary=kwargs["role"],
            )
        )

    monkeypatch.setattr(
        "control_plane.customers.application.create_customer.deliver_invitation",
        _capture_deliver,
    )
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "SA3 B", "oa-sa3b@vokit.test")
    owner_email = "accept-sa3@vokit.test"
    created = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency["id"], "Accept Me", owner_email=owner_email),
    )
    assert created.status_code == 201
    assert created.json()["data"]["status"] == "invited"
    assert "token" in captured
    guest = _client()
    accepted = _post(
        guest,
        "/api/v1/auth/invitations/accept",
        {"token": captured["token"], "password": PASSWORD},
    )
    assert accepted.status_code == 201
    detail = platform.get(f"/api/v1/platform/customers/{created.json()['data']['id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["status"] == "active"


@pytest.mark.django_db
def test_suspend_requires_reason_and_records_audit() -> None:
    from control_plane.audit.models import AuditEvent

    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "SA3 C", "oa-sa3c@vokit.test")
    created = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency["id"], "Suspend Me"),
    )
    customer_id = created.json()["data"]["id"]
    _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/status",
        {"action": "activate"},
    )
    missing = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/status",
        {"action": "suspend"},
    )
    assert missing.status_code == 400
    suspended = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/status",
        {"action": "suspend", "reason": "policy hold"},
    )
    assert suspended.status_code == 200
    assert suspended.json()["data"]["status"] == "suspended"
    assert AuditEvent.objects.filter(
        action="customer.status.changed", entity_id=customer_id
    ).exists()


@pytest.mark.django_db
def test_platform_usage_and_minutes_adjustment() -> None:
    from control_plane.audit.models import AuditEvent

    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "SA3 D", "oa-sa3d@vokit.test")
    created = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency["id"], "Minutes Co"),
    )
    customer_id = created.json()["data"]["id"]
    usage = platform.get(f"/api/v1/platform/customers/{customer_id}/usage")
    assert usage.status_code == 200
    assert usage.json()["data"]["remaining_minutes"] == 0
    missing_reason = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/minutes-adjustment",
        {"minutes": 25},
    )
    assert missing_reason.status_code == 400
    credited = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/minutes-adjustment",
        {"minutes": 25, "reason": "goodwill credit"},
    )
    assert credited.status_code == 201
    assert credited.json()["data"]["remaining_minutes"] == 25
    kinds = {lot["kind"] for lot in credited.json()["data"]["lots"]}
    assert "adjustment" in kinds
    debited = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/minutes-adjustment",
        {"minutes": -10, "reason": "correction"},
    )
    assert debited.status_code == 201
    assert debited.json()["data"]["remaining_minutes"] == 15
    assert AuditEvent.objects.filter(action="customer.minutes.adjusted").exists()
    detail = platform.get(f"/api/v1/platform/customers/{customer_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["remaining_minutes"] == 15


@pytest.mark.django_db
def test_get_subscription_before_and_after_assign() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "SA3 E", "oa-sa3e@vokit.test")
    created = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency["id"], "Sub Co"),
    )
    customer_id = created.json()["data"]["id"]
    empty = platform.get(f"/api/v1/platform/customers/{customer_id}/subscription")
    assert empty.status_code == 200
    assert empty.json()["data"] is None
    plan = _post(
        platform,
        "/api/v1/platform/plans",
        {
            "name": "SA3 Plan",
            "price_minor": 5000,
            "included_minutes": 40,
            "allow_topups": False,
            "topup_minutes": 0,
            "topup_price_minor": 0,
            "overage_enabled": False,
            "overage_price_per_minute_minor": 0,
            "grace_seconds": 0,
        },
    )
    version_id = plan.json()["data"]["versions"][0]["id"]
    assigned = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/subscription",
        {"plan_version_id": version_id},
    )
    assert assigned.status_code == 201
    current = platform.get(f"/api/v1/platform/customers/{customer_id}/subscription")
    assert current.status_code == 200
    assert current.json()["data"]["plan_version_id"] == version_id
    assert current.json()["data"]["included_minutes"] == 40


@pytest.mark.django_db
def test_owner_conflict_on_duplicate_membership_email() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "SA3 F", "oa-sa3f@vokit.test")
    taken = "taken-owner@vokit.test"
    _user(taken, PrincipalType.AGENCY, "agency_owner", uuid.UUID(agency["id"]))
    conflict = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency["id"], "Conflict", owner_email=taken),
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "owner_conflict"
