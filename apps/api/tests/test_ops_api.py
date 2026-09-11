from __future__ import annotations

import json
import uuid

import pytest
from django.core import mail
from django.test import Client

from control_plane.audit.infrastructure.container import audit_events
from control_plane.audit.models import AuditEvent
from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.kyc.infrastructure.hmac import sign_kyc_body
from control_plane.platform_settings.infrastructure.container import platform_settings
from shared_kernel.errors import DomainError
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


def _patch(client: Client, path: str, payload: dict):
    return client.patch(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=_csrf(client),
    )


def _put(client: Client, path: str, payload: dict):
    return client.put(
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


def _kyc_webhook(payload: dict):
    body = json.dumps(payload).encode()
    client = Client(enforce_csrf_checks=True)
    return client.post(
        "/webhooks/kyc/external/v1/",
        data=body,
        content_type="application/json",
        HTTP_X_VOKIT_KYC_SIGNATURE=sign_kyc_body(
            secret_ref="KYC_WEBHOOK_SECRET", raw_body=body
        ),
    )


def _pair() -> dict:
    _user("platform-ops@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform-ops@vokit.test")
    agency_a = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Ops A",
            "legal_name": "Ops A",
            "owner_email": "oa-ops@vokit.test",
            "database": tenant_db_payload("oa-ops@vokit.test"),
        },
    )
    agency_b = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Ops B",
            "legal_name": "Ops B",
            "owner_email": "ob-ops@vokit.test",
            "database": tenant_db_payload("ob-ops@vokit.test"),
        },
    )
    agency_a_id = uuid.UUID(agency_a.json()["data"]["id"])
    agency_b_id = uuid.UUID(agency_b.json()["data"]["id"])
    customer_a = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Ops Cust A", "agency_id": str(agency_a_id)},
    )
    customer_b = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Ops Cust B", "agency_id": str(agency_a_id)},
    )
    customer_a_id = uuid.UUID(customer_a.json()["data"]["id"])
    customer_b_id = uuid.UUID(customer_b.json()["data"]["id"])
    _user("agency-a-ops@vokit.test", PrincipalType.AGENCY, "agency_owner", agency_a_id)
    _user("agency-b-ops@vokit.test", PrincipalType.AGENCY, "agency_owner", agency_b_id)
    _user(
        "cust-a-ops@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        agency_a_id,
        customer_a_id,
    )
    _user(
        "cust-b-ops@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        agency_a_id,
        customer_b_id,
    )
    agency_a_client = _client()
    agency_b_client = _client()
    client_a = _client()
    client_b = _client()
    _login(agency_a_client, "agency-a-ops@vokit.test")
    _login(agency_b_client, "agency-b-ops@vokit.test")
    _login(client_a, "cust-a-ops@vokit.test")
    _login(client_b, "cust-b-ops@vokit.test")
    return {
        "platform": platform,
        "agency_a_id": agency_a_id,
        "agency_b_id": agency_b_id,
        "customer_a_id": customer_a_id,
        "customer_b_id": customer_b_id,
        "agency_a": agency_a_client,
        "agency_b": agency_b_client,
        "client_a": client_a,
        "client_b": client_b,
    }


@pytest.mark.django_db
def test_mandatory_notice_cannot_be_disabled_and_still_delivers() -> None:
    ctx = _pair()
    denied = _put(
        ctx["agency_a"],
        "/api/v1/agency/notification-preferences",
        {"preferences": [{"event_type": "kyc.approved", "email": False, "in_app": False}]},
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "mandatory_notice"
    allowed = _put(
        ctx["agency_a"],
        "/api/v1/agency/notification-preferences",
        {
            "preferences": [
                {"event_type": "announcement.platform", "email": False, "in_app": True}
            ]
        },
    )
    assert allowed.status_code == 200
    session = _post(ctx["agency_a"], "/api/v1/agency/kyc/session", {})
    assert session.status_code in {200, 201}
    _kyc_webhook(
        {
            "event_id": str(new_uuid7()),
            "session_id": session.json()["data"]["session_id"],
            "status": "verified",
        }
    )
    inbox = ctx["agency_a"].get("/api/v1/agency/notifications")
    assert inbox.status_code == 200
    assert any(item["event_type"] == "kyc.approved" for item in inbox.json()["data"])


@pytest.mark.django_db
def test_foreign_inbox_is_not_found() -> None:
    ctx = _pair()
    announced = _post(
        ctx["platform"],
        "/api/v1/platform/announcements",
        {
            "title": "Agency A only",
            "body": "Scoped notice",
            "agency_id": str(ctx["agency_a_id"]),
            "reason": "ops",
        },
    )
    assert announced.status_code == 201
    inbox_a = ctx["agency_a"].get("/api/v1/agency/notifications")
    assert inbox_a.status_code == 200
    assert inbox_a.json()["data"]
    note_id = inbox_a.json()["data"][0]["id"]
    inbox_b = ctx["agency_b"].get("/api/v1/agency/notifications")
    assert inbox_b.json()["data"] == []
    foreign = _post(
        ctx["agency_b"],
        f"/api/v1/agency/notifications/{note_id}/read",
        {},
    )
    assert foreign.status_code == 404
    customer = _post(
        ctx["platform"],
        "/api/v1/platform/announcements",
        {
            "title": "Customer A only",
            "body": "Scoped customer notice",
            "customer_id": str(ctx["customer_a_id"]),
            "reason": "ops",
        },
    )
    assert customer.status_code == 201
    seen = ctx["client_a"].get("/api/v1/customer/notifications")
    hidden = ctx["client_b"].get("/api/v1/customer/notifications")
    assert seen.json()["data"]
    assert hidden.json()["data"] == []
    other = _post(
        ctx["client_b"],
        f"/api/v1/customer/notifications/{seen.json()['data'][0]['id']}/read",
        {},
    )
    assert other.status_code == 404


@pytest.mark.django_db
def test_audit_is_append_only_and_platform_searchable() -> None:
    ctx = _pair()
    changed = _patch(
        ctx["platform"],
        "/api/v1/platform/settings",
        {"key": "payout.hold_days", "value": 21, "reason": "hold policy"},
    )
    assert changed.status_code == 200
    assert platform_settings().hold_days() == 21
    agency = ctx["agency_a"].get("/api/v1/platform/audit-events")
    assert agency.status_code == 403
    found = ctx["platform"].get("/api/v1/platform/audit-events?action=settings.changed")
    assert found.status_code == 200
    rows = found.json()["data"]
    assert rows
    assert rows[0]["reason"] == "hold policy"
    event_id = rows[0]["id"]
    patched = _patch(
        ctx["platform"],
        f"/api/v1/platform/audit-events/{event_id}",
        {"action": "hacked"},
    )
    assert patched.status_code == 409
    deleted = ctx["platform"].delete(
        f"/api/v1/platform/audit-events/{event_id}",
        HTTP_X_CSRFTOKEN=_csrf(ctx["platform"]),
    )
    assert deleted.status_code == 409
    with pytest.raises(DomainError) as exc:
        audit_events().update()
    assert exc.value.code == "audit_immutable"
    row = AuditEvent.objects.get(id=event_id)
    row.action = "hacked"
    with pytest.raises(DomainError):
        row.save()
    with pytest.raises(DomainError):
        AuditEvent.objects.all().delete()


@pytest.mark.django_db
def test_kyc_override_is_audited_and_secrets_stay_out() -> None:
    ctx = _pair()
    session = _post(ctx["agency_a"], "/api/v1/agency/kyc/session", {})
    _kyc_webhook(
        {
            "event_id": str(new_uuid7()),
            "session_id": session.json()["data"]["session_id"],
            "status": "verified",
        }
    )
    cases = ctx["platform"].get("/api/v1/platform/kyc/cases")
    case_id = cases.json()["data"][0]["id"]
    frozen = _post(
        ctx["platform"],
        f"/api/v1/platform/kyc/cases/{case_id}/override",
        {"action": "freeze", "internal_note": "risk review", "api_key": "should-redact"},
    )
    assert frozen.status_code == 200
    found = ctx["platform"].get("/api/v1/platform/audit-events?action=kyc.override")
    assert found.status_code == 200
    row = found.json()["data"][0]
    assert row["reason"] == "risk review"
    assert row["severity"] == "high"
    assert "should-redact" not in json.dumps(row)


@pytest.mark.django_db
def test_settings_are_platform_only_and_secrets_masked() -> None:
    ctx = _pair()
    denied = ctx["agency_a"].get("/api/v1/platform/settings")
    assert denied.status_code == 403
    snap = ctx["platform"].get("/api/v1/platform/settings")
    assert snap.status_code == 200
    keys = {item["key"]: item for item in snap.json()["data"]["settings"]}
    assert keys["payout.hold_days"]["value"] == 15
    assert keys["telephony.stt_api_key_ref"]["value"] is None
    assert keys["telephony.stt_api_key_ref"]["secret"] is True
    flagged = _post(
        ctx["platform"],
        "/api/v1/platform/settings/flags",
        {
            "agency_id": str(ctx["agency_a_id"]),
            "flag": "outbound",
            "enabled": False,
            "reason": "canary off",
        },
    )
    assert flagged.status_code == 200
    flags = flagged.json()["data"]["agency_flags"]
    assert flags[0]["flag"] == "outbound"
    assert flags[0]["enabled"] is False


@pytest.mark.django_db
def test_invitation_email_contains_token_not_logged_in_app() -> None:
    ctx = _pair()
    invited = _post(
        ctx["agency_a"],
        "/api/v1/agency/team",
        {"email": "new-ops@vokit.test", "role": "agency_admin"},
    )
    assert invited.status_code == 201
    token = invited.json()["data"]["token"]
    assert token
    assert mail.outbox
    assert token in mail.outbox[-1].body
    inbox = ctx["agency_a"].get("/api/v1/agency/notifications")
    bodies = " ".join(item["body"] for item in inbox.json()["data"])
    assert token not in bodies
    deliveries = ctx["platform"].get("/api/v1/platform/notification-deliveries")
    assert deliveries.status_code == 200
    assert token not in json.dumps(deliveries.json()["data"])
