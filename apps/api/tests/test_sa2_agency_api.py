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
from control_plane.tenancy.models import Tenant, TenantDatabase
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


def _patch(client: Client, path: str, payload: dict):
    return client.patch(
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
        event_type="invitation.agency",
        recipient_email="owner-invite@vokit.test",
        status="sent",
    ).exists()
    assert len(mail.outbox) >= 1


@pytest.mark.django_db
def test_agency_create_owner_conflict() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    _user("taken@vokit.test", PrincipalType.PLATFORM, "support_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    before_tenants = Tenant.objects.count()
    before_dbs = TenantDatabase.objects.count()
    payload = tenant_db_payload("taken@vokit.test")
    response = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Conflict Co",
            "legal_name": "Conflict Co",
            "owner_email": "taken@vokit.test",
            "database": payload,
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "owner_conflict"
    assert Tenant.objects.count() == before_tenants
    assert TenantDatabase.objects.count() == before_dbs
    assert not TenantDatabase.objects.filter(db_username=payload["username"]).exists()
    listed = client.get("/api/v1/platform/agencies?name=Conflict Co")
    assert listed.status_code == 200
    assert listed.json()["data"] == []


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
        {"commission_rate_bps": 2500, "reason": "rate change"},
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
    _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate", "confirm": True},
    )
    restricted = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "restrict", "reason": "manual review", "confirm": True},
    )
    assert restricted.status_code == 200
    caps = restricted.json()["data"]["capabilities"]
    assert caps["create_customers"] is False
    assert caps["request_payouts"] is False
    assert AuditEvent.objects.filter(
        action="agency.status.changed", entity_id=agency_id
    ).exists()
    _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate", "confirm": True},
    )
    reviewed = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "review", "reason": "kyc review", "confirm": True},
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
        {"capabilities": {"create_customers": False}, "confirm": True, "reason": "gate customers"},
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
    _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate", "confirm": True},
    )
    _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/capabilities",
        {"capabilities": {"create_agents": False}, "confirm": True, "reason": "gate agents"},
    )
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency_id, "Cust"),
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
    assert privileged.status_code == 409
    assert privileged.json()["error"]["code"] == "agency_cannot_create_agent"


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


@pytest.mark.django_db
def test_agency_and_customer_cannot_list_platform_agencies() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    created = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Iso List",
            "legal_name": "Iso List",
            "owner_email": "iso-list-owner@vokit.test",
            "database": tenant_db_payload("iso-list-owner@vokit.test"),
        },
    )
    agency_id = uuid.UUID(created.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency_id, "Iso Cust"),
    )
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    _user("iso-agency@vokit.test", PrincipalType.AGENCY, "agency_owner", agency_id)
    _user(
        "iso-customer@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        agency_id,
        customer_id,
    )
    invalid = platform.get("/api/v1/platform/agencies?status=not-a-status")
    assert invalid.status_code == 400
    agency = _client()
    _login(agency, "iso-agency@vokit.test")
    assert agency.get("/api/v1/platform/agencies").status_code == 403
    customer_client = _client()
    _login(customer_client, "iso-customer@vokit.test")
    assert customer_client.get("/api/v1/platform/agencies").status_code == 403


@pytest.mark.django_db
def test_profile_patch_and_finance_mrr() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    created = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Mrr Co",
            "legal_name": "Mrr Co",
            "owner_email": "mrr-owner@vokit.test",
            "commission_rate_bps": 1000,
            "database": tenant_db_payload("mrr-owner@vokit.test"),
        },
    )
    agency_id = created.json()["data"]["id"]
    patched = _patch(
        client,
        f"/api/v1/platform/agencies/{agency_id}",
        {"display_name": "Mrr Co Legal", "legal_name": "Mrr Co LLC"},
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["display_name"] == "Mrr Co Legal"
    assert AuditEvent.objects.filter(
        action="agency.profile.changed", entity_id=agency_id
    ).exists()
    detail = client.get(f"/api/v1/platform/agencies/{agency_id}")
    assert "notes" not in detail.json()["data"]
    _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate", "confirm": True},
    )
    customer = _post(
        client,
        "/api/v1/platform/customers",
        platform_customer_body(uuid.UUID(agency_id), "Mrr Cust"),
    )
    customer_id = customer.json()["data"]["id"]
    plan = _post(
        client,
        "/api/v1/platform/plans",
        {
            "name": "Mrr Plan",
            "price_minor": 10000,
            "included_minutes": 100,
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
        client,
        f"/api/v1/platform/customers/{customer_id}/subscription",
        {"plan_version_id": version_id},
    )
    assert assigned.status_code == 201
    finance = client.get(f"/api/v1/platform/agencies/{agency_id}/finance")
    assert finance.status_code == 200
    data = finance.json()["data"]
    assert data["mrr_minor"] == 10000
    assert data["commission_mrr_minor"] == 1000


@pytest.mark.django_db
def test_phone_numbers_filter_by_agency_id() -> None:
    from control_plane.telephony.models import PhoneNumber

    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    first = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Num A",
            "legal_name": "Num A",
            "owner_email": "num-a-owner@vokit.test",
            "database": tenant_db_payload("num-a-owner@vokit.test"),
        },
    )
    second = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Num B",
            "legal_name": "Num B",
            "owner_email": "num-b-owner@vokit.test",
            "database": tenant_db_payload("num-b-owner@vokit.test"),
        },
    )
    agency_a = uuid.UUID(first.json()["data"]["id"])
    agency_b = uuid.UUID(second.json()["data"]["id"])
    one = _post(
        client,
        "/api/v1/platform/phone-numbers",
        {
            "e164": "+14155550111",
            "country": "US",
            "area": "415",
            "monthly_cost_minor": 500,
            "capabilities": ["voice"],
        },
    )
    two = _post(
        client,
        "/api/v1/platform/phone-numbers",
        {
            "e164": "+14155550112",
            "country": "US",
            "area": "415",
            "monthly_cost_minor": 500,
            "capabilities": ["voice"],
        },
    )
    PhoneNumber.objects.filter(id=one.json()["data"]["id"]).update(
        assigned_tenant_id=agency_a
    )
    PhoneNumber.objects.filter(id=two.json()["data"]["id"]).update(
        assigned_tenant_id=agency_b
    )
    listed = client.get(f"/api/v1/platform/phone-numbers?agency_id={agency_a}")
    assert listed.status_code == 200
    ids = {row["id"] for row in listed.json()["data"]}
    assert one.json()["data"]["id"] in ids
    assert two.json()["data"]["id"] not in ids


@pytest.mark.django_db
def test_commission_future_date_and_agency_forbidden() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    created = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Rate Future",
            "legal_name": "Rate Future",
            "owner_email": "rate-future-owner@vokit.test",
            "commission_rate_bps": 500,
            "database": tenant_db_payload("rate-future-owner@vokit.test"),
        },
    )
    agency_id = created.json()["data"]["id"]
    missing_reason = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/commission",
        {"commission_rate_bps": 2500},
    )
    assert missing_reason.status_code == 400
    past = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/commission",
        {
            "commission_rate_bps": 2500,
            "reason": "backdate",
            "rate_effective_at": "2020-01-01T00:00:00+00:00",
        },
    )
    assert past.status_code == 400
    future = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/commission",
        {
            "commission_rate_bps": 2500,
            "reason": "scheduled increase",
            "rate_effective_at": "2099-01-01T00:00:00+00:00",
        },
    )
    assert future.status_code == 200
    body = future.json()["data"]
    assert body["commission_rate_bps"] == 2500
    assert body["previous_commission_rate_bps"] == 500
    assert body["rate_effective_at"].startswith("2099-01-01")
    _user(
        "rate-agency@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        uuid.UUID(agency_id),
    )
    agency = _client()
    _login(agency, "rate-agency@vokit.test")
    denied = _post(
        agency,
        f"/api/v1/platform/agencies/{agency_id}/commission",
        {"commission_rate_bps": 100, "reason": "self edit"},
    )
    assert denied.status_code == 403


@pytest.mark.django_db
def test_status_confirm_suspend_gates_and_capabilities_audit() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    client = _client()
    _login(client, "platform@vokit.test")
    created = _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": "Gate Suspend",
            "legal_name": "Gate Suspend",
            "owner_email": "gate-suspend@vokit.test",
            "database": tenant_db_payload("gate-suspend@vokit.test"),
        },
    )
    agency_id = created.json()["data"]["id"]
    unconfirmed = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate"},
    )
    assert unconfirmed.status_code == 400
    _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate", "confirm": True},
    )
    suspended = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "suspend", "confirm": True, "reason": "risk hold"},
    )
    assert suspended.status_code == 200
    caps = suspended.json()["data"]["capabilities"]
    assert caps["create_customers"] is False
    assert caps["create_agents"] is False
    assert caps["purchase_numbers"] is False
    assert caps["request_payouts"] is False
    assert caps["existing_customer_services"] is True
    changed = _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/capabilities",
        {
            "capabilities": {"create_agents": True},
            "confirm": True,
            "reason": "restore agents",
        },
    )
    assert changed.status_code == 200
    assert AuditEvent.objects.filter(
        action="agency.capabilities.changed", entity_id=agency_id
    ).exists()


@pytest.mark.django_db
def test_notes_are_platform_only() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    created = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Notes Iso",
            "legal_name": "Notes Iso",
            "owner_email": "notes-iso-owner@vokit.test",
            "database": tenant_db_payload("notes-iso-owner@vokit.test"),
        },
    )
    agency_id = uuid.UUID(created.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency_id, "Notes Cust"),
    )
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    missing = platform.get(
        "/api/v1/platform/agencies/00000000-0000-7000-8000-000000000099/notes"
    )
    assert missing.status_code == 404
    _user("notes-agency@vokit.test", PrincipalType.AGENCY, "agency_owner", agency_id)
    _user(
        "notes-customer@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        agency_id,
        customer_id,
    )
    agency = _client()
    _login(agency, "notes-agency@vokit.test")
    assert agency.get(f"/api/v1/platform/agencies/{agency_id}/notes").status_code == 403
    denied_post = _post(
        agency,
        f"/api/v1/platform/agencies/{agency_id}/notes",
        {"body": "should not work", "risk_flag": True},
    )
    assert denied_post.status_code == 403
    customer_client = _client()
    _login(customer_client, "notes-customer@vokit.test")
    assert (
        customer_client.get(f"/api/v1/platform/agencies/{agency_id}/notes").status_code
        == 403
    )


@pytest.mark.django_db
def test_restricted_agency_actor_cannot_create_agent() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    created = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Restrict Agents",
            "legal_name": "Restrict Agents",
            "owner_email": "restrict-agents@vokit.test",
            "database": tenant_db_payload("restrict-agents@vokit.test"),
        },
    )
    agency_id = created.json()["data"]["id"]
    _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate", "confirm": True},
    )
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency_id, "Restrict Cust"),
    )
    customer_id = customer.json()["data"]["id"]
    restricted = _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "restrict", "confirm": True, "reason": "manual restriction"},
    )
    assert restricted.status_code == 200
    _user(
        "agency-restrict-agents@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        uuid.UUID(agency_id),
    )
    agency = _client()
    _login(agency, "agency-restrict-agents@vokit.test")
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
def test_restrict_notifies_agency_review_does_not() -> None:
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    created = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Notice Co",
            "legal_name": "Notice Co",
            "owner_email": "notice-owner@vokit.test",
            "database": tenant_db_payload("notice-owner@vokit.test"),
        },
    )
    agency_id = created.json()["data"]["id"]
    _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate", "confirm": True},
    )
    _user(
        "agency-notice@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        uuid.UUID(agency_id),
    )
    agency = _client()
    _login(agency, "agency-notice@vokit.test")
    restricted = _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "restrict", "confirm": True, "reason": "restriction notice"},
    )
    assert restricted.status_code == 200
    inbox = agency.get("/api/v1/agency/notifications")
    assert inbox.status_code == 200
    events = [item["event_type"] for item in inbox.json()["data"]]
    assert events.count("agency.suspended") == 1
    reviewed = _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "review", "confirm": True, "reason": "under review"},
    )
    assert reviewed.status_code == 200
    after = agency.get("/api/v1/agency/notifications")
    later = [item["event_type"] for item in after.json()["data"]]
    assert later.count("agency.suspended") == 1
