from __future__ import annotations

import json
import uuid

import pytest
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.integrations.infrastructure.container import (
    integration_adapter,
    webhook_transport,
)
from control_plane.telephony.infrastructure.container import reset_sip_edge
from shared_kernel.hmac import sign_hmac_raw
from shared_kernel.ids import new_uuid7
from tests.tenant_db_fixtures import tenant_db_payload

PASSWORD = "Phase2-Demo!ok"
TEL_TOKEN = "test-internal-telephony-token"


def _client() -> Client:
    return Client(enforce_csrf_checks=True)


def _csrf(client: Client) -> str:
    return client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]


def _post(client: Client, path: str, payload: dict, **headers):
    extra = {"HTTP_X_CSRFTOKEN": _csrf(client)}
    extra.update(headers)
    return client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        **extra,
    )


def _internal(path: str, payload: dict | None = None):
    client = Client(enforce_csrf_checks=True)
    return client.post(
        path,
        data=json.dumps(payload or {}),
        content_type="application/json",
        HTTP_X_VOKIT_INTERNAL_TOKEN=TEL_TOKEN,
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


def _ready_pair() -> dict:
    _user("platform-int@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform-int@vokit.test")
    agency = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Int A",
            "legal_name": "Int A",
            "owner_email": "oa-int@vokit.test",
            "database": tenant_db_payload("oa-int@vokit.test"),
        },
    )
    assert agency.status_code == 201
    agency_id = uuid.UUID(agency.json()["data"]["id"])
    activated = _post(
        platform,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate"},
    )
    assert activated.status_code == 200
    customer_a = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Cust A", "agency_id": str(agency_id)},
    )
    customer_b = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Cust B", "agency_id": str(agency_id)},
    )
    customer_a_id = uuid.UUID(customer_a.json()["data"]["id"])
    customer_b_id = uuid.UUID(customer_b.json()["data"]["id"])
    _user(
        "agency-int@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=agency_id,
    )
    agency_client = _client()
    _login(agency_client, "agency-int@vokit.test")
    _user(
        "cust-a-int@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        tenant_id=agency_id,
        customer_id=customer_a_id,
    )
    _user(
        "cust-b-int@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        tenant_id=agency_id,
        customer_id=customer_b_id,
    )
    client_a = _client()
    client_b = _client()
    _login(client_a, "cust-a-int@vokit.test")
    _login(client_b, "cust-b-int@vokit.test")
    return {
        "platform": platform,
        "agency_client": agency_client,
        "agency_id": agency_id,
        "customer_a_id": customer_a_id,
        "customer_b_id": customer_b_id,
        "client_a": client_a,
        "client_b": client_b,
    }


def _connect(agency_client, customer_id: uuid.UUID, provider: str = "hubspot"):
    return _post(
        agency_client,
        "/api/v1/agency/integrations",
        {
            "customer_id": str(customer_id),
            "provider": provider,
            "credential": "refresh-token-lab-1",
        },
    )


@pytest.mark.django_db
def test_customer_a_cannot_use_customer_b_connection() -> None:
    ctx = _ready_pair()
    created_a = _connect(ctx["agency_client"], ctx["customer_a_id"])
    created_b = _connect(ctx["agency_client"], ctx["customer_b_id"])
    assert created_a.status_code == 201
    assert created_b.status_code == 201
    assert "credential" not in created_a.json()["data"]
    id_a = created_a.json()["data"]["id"]
    id_b = created_b.json()["data"]["id"]

    listed_a = ctx["client_a"].get("/api/v1/customer/integrations")
    assert {row["id"] for row in listed_a.json()["data"]} == {id_a}
    listed_b = ctx["client_b"].get("/api/v1/customer/integrations")
    assert {row["id"] for row in listed_b.json()["data"]} == {id_b}

    stolen = _post(
        ctx["client_a"],
        f"/api/v1/customer/integrations/{id_b}/test",
        {},
    )
    assert stolen.status_code == 404

    forbidden_connect = _post(
        ctx["client_a"],
        "/api/v1/customer/integrations",
        {"provider": "salesforce", "credential": "should-not-store"},
    )
    assert forbidden_connect.status_code == 403
    enabled = _post(
        ctx["agency_client"],
        "/api/v1/agency/integrations/settings",
        {"customer_id": str(ctx["customer_a_id"]), "self_service": True},
    )
    assert enabled.json()["data"]["self_service"] is True
    self_serve = _post(
        ctx["client_a"],
        "/api/v1/customer/integrations",
        {"provider": "salesforce", "credential": "customer-a-own-token"},
    )
    assert self_serve.status_code == 201
    assert self_serve.json()["data"]["customer_id"] == str(ctx["customer_a_id"])

    agency_b_only = ctx["agency_client"].get(
        f"/api/v1/agency/integrations?customer_id={ctx['customer_b_id']}"
    )
    assert {row["id"] for row in agency_b_only.json()["data"]} == {id_b}


@pytest.mark.django_db
def test_tool_gateway_and_webhooks_stay_customer_scoped() -> None:
    reset_sip_edge()
    ctx = _ready_pair()
    plan = _post(
        ctx["platform"],
        "/api/v1/platform/plans",
        {
            "name": "Int Plan",
            "price_minor": 10000,
            "included_minutes": 100,
            "allow_topups": False,
            "topup_minutes": 0,
            "topup_price_minor": 0,
            "overage_enabled": False,
            "overage_price_per_minute_minor": 10,
            "grace_seconds": 30,
        },
    )
    version_id = plan.json()["data"]["versions"][0]["id"]
    for customer_id in (ctx["customer_a_id"], ctx["customer_b_id"]):
        assigned = _post(
            ctx["platform"],
            f"/api/v1/platform/customers/{customer_id}/subscription",
            {"plan_version_id": version_id},
        )
        assert assigned.status_code == 201
    created = _post(
        ctx["agency_client"],
        "/api/v1/agency/agents",
        {"customer_id": str(ctx["customer_a_id"]), "display_name": "Int bot"},
    )
    agent_id = created.json()["data"]["id"]
    configured = ctx["agency_client"].patch(
        f"/api/v1/agency/agents/{agent_id}",
        data=json.dumps(
            {
                "voice_provider": "elevenlabs",
                "voice_id": "voice-1",
                "language": "en",
                "fallback_behavior": "hangup",
                "recording_disclosure": True,
                "instructions": "Answer briefly.",
                "tools": ["create_lead"],
                "inbound_enabled": True,
                "greeting": "Hello.",
            }
        ),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=_csrf(ctx["agency_client"]),
    )
    assert configured.status_code == 200
    published = _post(ctx["agency_client"], f"/api/v1/agency/agents/{agent_id}/publish", {})
    assert published.status_code == 200
    stocked = _post(
        ctx["platform"],
        "/api/v1/platform/phone-numbers",
        {"e164": "+14155550999", "country": "US", "monthly_cost_minor": 100},
    )
    reserved = _post(
        ctx["agency_client"],
        "/api/v1/agency/phone-numbers/reservations",
        {"number_id": stocked.json()["data"]["id"], "agent_id": agent_id},
    )
    assigned_number = _post(
        ctx["agency_client"],
        "/api/v1/agency/phone-numbers/assignments",
        {"reservation_id": reserved.json()["data"]["id"], "confirm": True},
        HTTP_IDEMPOTENCY_KEY="int-did-1",
    )
    assert assigned_number.status_code == 201
    conn_a = _connect(ctx["agency_client"], ctx["customer_a_id"])
    conn_b = _connect(ctx["agency_client"], ctx["customer_b_id"])
    hook = _post(
        ctx["agency_client"],
        "/api/v1/agency/webhooks",
        {
            "customer_id": str(ctx["customer_a_id"]),
            "url": "https://hooks.example.test/a",
            "events": ["call.completed", "agent.action.completed"],
        },
    )
    assert hook.status_code == 201
    secret = hook.json()["data"]["secret"]
    assert secret
    listed_hooks = ctx["agency_client"].get(
        f"/api/v1/agency/webhooks?customer_id={ctx['customer_b_id']}"
    )
    assert listed_hooks.json()["data"] == []

    inbound = _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": "+14155550999",
            "edge_call_id": "edge-int-1",
            "from_number": "+15550001111",
            "direction": "inbound",
        },
    )
    assert inbound.json()["data"]["admitted"] is True
    auto = _internal(
        "/internal/telephony/v1/tools/invoke/",
        {
            "edge_call_id": "edge-int-1",
            "tool": "create_lead",
            "arguments": {"name": "Ada"},
        },
    )
    assert auto.json()["data"]["ok"] is True
    stolen = _internal(
        "/internal/telephony/v1/tools/invoke/",
        {
            "edge_call_id": "edge-int-1",
            "tool": "create_lead",
            "arguments": {
                "connection_id": conn_b.json()["data"]["id"],
                "name": "Stolen",
            },
        },
    )
    assert stolen.json()["data"]["ok"] is False
    assert stolen.json()["data"]["error"] == "not_found"
    own = _internal(
        "/internal/telephony/v1/tools/invoke/",
        {
            "edge_call_id": "edge-int-1",
            "tool": "create_lead",
            "arguments": {
                "connection_id": conn_a.json()["data"]["id"],
                "name": "Ada",
            },
        },
    )
    assert own.json()["data"]["ok"] is True
    assert integration_adapter().calls[-1].customer_id == str(ctx["customer_a_id"])
    ended = _internal(
        "/internal/telephony/v1/voice-session/end/",
        {"edge_call_id": "edge-int-1", "reason": "completed", "status": "completed"},
    )
    assert ended.json()["data"]["ok"] is True
    deliveries = ctx["agency_client"].get(
        f"/api/v1/agency/webhooks/deliveries?customer_id={ctx['customer_a_id']}"
    )
    assert deliveries.status_code == 200
    rows = deliveries.json()["data"]
    assert any(row["event_type"] == "call.completed" for row in rows)
    assert all(row["customer_id"] == str(ctx["customer_a_id"]) for row in rows)
    assert webhook_transport().sent
    signed = webhook_transport().sent[-1]["headers"].get("X-Vokit-Signature", "")
    assert signed.startswith("sha256=")
    replay = _post(
        ctx["agency_client"],
        f"/api/v1/agency/webhooks/deliveries/{rows[0]['id']}/replay",
        {},
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["event_id"] == rows[0]["event_id"]
    assert replay.json()["data"]["id"] != rows[0]["id"]
    assert sign_hmac_raw(secret=secret, raw_body=b"x") != ""
