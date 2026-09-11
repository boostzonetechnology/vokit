from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import pytest
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.telephony.infrastructure.container import reset_sip_edge
from shared_kernel.ids import new_uuid7

from tests.tenant_db_fixtures import tenant_db_payload

PASSWORD = "Phase2-Demo!ok"
TOKEN = "test-internal-telephony-token"


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


def _internal(path: str, payload: dict | None = None, *, method: str = "post"):
    client = Client(enforce_csrf_checks=True)
    headers = {"HTTP_X_VOKIT_INTERNAL_TOKEN": TOKEN}
    data = json.dumps(payload or {})
    if method == "get":
        return client.get(path, payload or {}, **headers)
    return client.post(path, data=data, content_type="application/json", **headers)


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


def _ready_media(*, outbound: bool = False, hours: list | None = None):
    reset_sip_edge()
    _user("platform-media@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform-media@vokit.test")
    agency = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Media A",
            "legal_name": "Media A",
            "owner_email": "oa-media@vokit.test",
            "database": tenant_db_payload("oa-media@vokit.test"),
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
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Media Cust", "agency_id": str(agency_id)},
    )
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    plan = _post(
        platform,
        "/api/v1/platform/plans",
        {
            "name": "Media Plan",
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
    assigned = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/subscription",
        {"plan_version_id": version_id},
    )
    assert assigned.status_code == 201
    _user(
        "agency-media@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=agency_id,
    )
    agency_client = _client()
    _login(agency_client, "agency-media@vokit.test")
    created = _post(
        agency_client,
        "/api/v1/agency/agents",
        {"customer_id": str(customer_id), "display_name": "Media bot"},
    )
    agent_id = created.json()["data"]["id"]
    configured = agency_client.patch(
        f"/api/v1/agency/agents/{agent_id}",
        data=json.dumps(
            {
                "voice_provider": "elevenlabs",
                "voice_id": "voice-1",
                "language": "en",
                "fallback_behavior": "message",
                "recording_disclosure": True,
                "instructions": "Answer briefly.",
                "tools": ["transfer_call"],
                "inbound_enabled": True,
                "outbound_enabled": outbound,
                "greeting": "Hello from Vokit.",
                "voicemail_greeting": "Leave a message.",
                "outbound_voicemail_message": "Please call back.",
                "business_hours": hours or [],
            }
        ),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=_csrf(agency_client),
    )
    assert configured.status_code == 200
    published = _post(agency_client, f"/api/v1/agency/agents/{agent_id}/publish", {})
    assert published.status_code == 200
    stocked = _post(
        platform,
        "/api/v1/platform/phone-numbers",
        {"e164": "+14155550888", "country": "US", "monthly_cost_minor": 100},
    )
    reserved = _post(
        agency_client,
        "/api/v1/agency/phone-numbers/reservations",
        {"number_id": stocked.json()["data"]["id"], "agent_id": agent_id},
    )
    assigned_number = _post(
        agency_client,
        "/api/v1/agency/phone-numbers/assignments",
        {"reservation_id": reserved.json()["data"]["id"], "confirm": True},
        HTTP_IDEMPOTENCY_KEY="media-did-1",
    )
    assert assigned_number.status_code == 201
    return {
        "platform": platform,
        "agency_client": agency_client,
        "agency_id": agency_id,
        "customer_id": customer_id,
        "agent_id": agent_id,
        "did": "+14155550888",
    }


@pytest.mark.django_db
def test_inbound_and_outbound_calls_are_recorded_in_metadata() -> None:
    ctx = _ready_media(outbound=True)
    inbound = _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": ctx["did"],
            "edge_call_id": "edge-in-1",
            "from_number": "+15550001111",
            "sip_call_id": "sip-in",
            "direction": "inbound",
        },
    )
    assert inbound.status_code == 200
    assert inbound.json()["data"]["admitted"] is True
    ended_in = _internal(
        "/internal/telephony/v1/voice-session/end/",
        {"edge_call_id": "edge-in-1", "reason": "completed", "status": "completed"},
    )
    assert ended_in.json()["data"]["ok"] is True
    outbound = _post(
        ctx["agency_client"],
        "/api/v1/agency/calls/outbound",
        {"agent_id": ctx["agent_id"], "to": "+15551234567"},
        HTTP_IDEMPOTENCY_KEY="out-1",
    )
    assert outbound.status_code == 201
    edge_id = outbound.json()["data"]["edge_call_id"]
    assert outbound.json()["data"]["direction"] == "outbound"
    replay = _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": ctx["did"],
            "edge_call_id": edge_id,
            "from_number": ctx["did"],
            "direction": "outbound",
        },
    )
    assert replay.json()["data"]["admitted"] is True
    assert replay.json()["data"]["vokit_call_id"] == outbound.json()["data"]["vokit_call_id"]
    _internal(
        "/internal/telephony/v1/voice-session/end/",
        {"edge_call_id": edge_id, "reason": "completed", "status": "completed"},
    )
    listed = ctx["agency_client"].get("/api/v1/agency/calls")
    assert listed.status_code == 200
    directions = {row["direction"] for row in listed.json()["data"]}
    assert directions == {"inbound", "outbound"}
    assert all(row["status"] == "completed" for row in listed.json()["data"])


@pytest.mark.django_db
def test_transfer_e164_queue_and_sip_client() -> None:
    ctx = _ready_media()
    e164 = _post(
        ctx["agency_client"],
        "/api/v1/agency/transfers",
        {
            "customer_id": str(ctx["customer_id"]),
            "kind": "e164",
            "label": "Reception",
            "target": "+15550001002",
        },
    )
    assert e164.status_code == 201
    queue = _post(
        ctx["agency_client"],
        "/api/v1/agency/transfers",
        {
            "customer_id": str(ctx["customer_id"]),
            "kind": "queue",
            "label": "Support queue",
            "members": [
                {"kind": "e164", "target": "+15550009999", "label": "busy"},
                {"kind": "sip_client", "target": "1002", "label": "desk"},
            ],
        },
    )
    assert queue.status_code == 201
    patched = ctx["agency_client"].patch(
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        data=json.dumps({"default_transfer_id": e164.json()["data"]["id"]}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=_csrf(ctx["agency_client"]),
    )
    assert patched.status_code == 200
    _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": ctx["did"],
            "edge_call_id": "edge-xfer-1",
            "from_number": "+15550001111",
            "direction": "inbound",
        },
    )
    started = _internal(
        "/internal/telephony/v1/voice-session/transfer/",
        {"edge_call_id": "edge-xfer-1"},
    )
    assert started.json()["data"]["status"] == "pending"
    assert started.json()["data"]["kind"] == "e164"
    polled = _internal(
        "/internal/telephony/v1/voice-session/transfer/status/?edge_call_id=edge-xfer-1",
        {"edge_call_id": "edge-xfer-1"},
        method="get",
    )
    assert polled.json()["data"]["status"] == "completed"
    _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": ctx["did"],
            "edge_call_id": "edge-xfer-q",
            "from_number": "+15550001111",
            "direction": "inbound",
        },
    )
    hunted = _internal(
        "/internal/telephony/v1/voice-session/transfer/",
        {
            "edge_call_id": "edge-xfer-q",
            "destination_id": queue.json()["data"]["id"],
        },
    )
    assert hunted.json()["data"]["ok"] is True
    assert hunted.json()["data"]["to"] == "1002"
    foreign = _post(
        ctx["platform"],
        "/api/v1/platform/agencies",
        {
            "display_name": "Media B",
            "legal_name": "Media B",
            "owner_email": "oa-media-b@vokit.test",
            "database": tenant_db_payload("oa-media-b@vokit.test"),
        },
    )
    other_id = uuid.UUID(foreign.json()["data"]["id"])
    _user(
        "agency-media-b@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=other_id,
    )
    other = _client()
    _login(other, "agency-media-b@vokit.test")
    listed = other.get("/api/v1/agency/transfers")
    assert listed.status_code == 200
    assert listed.json()["data"] == []


@pytest.mark.django_db
def test_after_hours_inbound_and_outbound_voicemail_metadata() -> None:
    tomorrow = (datetime.now(UTC).weekday() + 1) % 7
    ctx = _ready_media(
        outbound=True,
        hours=[{"weekday": tomorrow, "start": "09:00", "end": "17:00"}],
    )
    resolved = _internal("/internal/telephony/v1/did/resolve/", {"did": ctx["did"]})
    assert resolved.json()["data"]["routable"] is True
    bootstrap = _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": ctx["did"],
            "edge_call_id": "edge-vm-in",
            "from_number": "+15550001111",
            "direction": "inbound",
        },
    )
    assert bootstrap.json()["data"]["voicemail"]["required"] is True
    started = _internal(
        "/internal/telephony/v1/voice-session/voicemail/",
        {"edge_call_id": "edge-vm-in", "direction": "inbound", "action": "start"},
    )
    assert started.json()["data"]["status"] == "recording"
    completed = _internal(
        "/internal/telephony/v1/voice-session/voicemail/",
        {
            "edge_call_id": "edge-vm-in",
            "direction": "inbound",
            "action": "complete",
            "duration_seconds": 12,
        },
    )
    assert completed.json()["data"]["status"] == "ready"
    assert completed.json()["data"]["object_ref"] == ""
    _internal(
        "/internal/telephony/v1/voice-session/end/",
        {"edge_call_id": "edge-vm-in", "reason": "voicemail", "status": "completed"},
    )
    outbound = _post(
        ctx["agency_client"],
        "/api/v1/agency/calls/outbound",
        {"agent_id": ctx["agent_id"], "to": "+15557654321"},
        HTTP_IDEMPOTENCY_KEY="out-vm-1",
    )
    edge_id = outbound.json()["data"]["edge_call_id"]
    _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {"did": ctx["did"], "edge_call_id": edge_id, "direction": "outbound"},
    )
    left = _internal(
        "/internal/telephony/v1/voice-session/voicemail/",
        {
            "edge_call_id": edge_id,
            "direction": "outbound",
            "action": "complete",
            "duration_seconds": 8,
        },
    )
    assert left.json()["data"]["ok"] is True
    listed = ctx["agency_client"].get("/api/v1/agency/calls")
    voicemail_rows = [row for row in listed.json()["data"] if row["voicemail_status"]]
    assert {row["direction"] for row in voicemail_rows} == {"inbound", "outbound"}


@pytest.mark.django_db
def test_platform_can_disable_transfer_destination() -> None:
    ctx = _ready_media()
    created = _post(
        ctx["agency_client"],
        "/api/v1/agency/transfers",
        {
            "customer_id": str(ctx["customer_id"]),
            "kind": "sip_client",
            "label": "Desk",
            "target": "1002",
        },
    )
    dest_id = created.json()["data"]["id"]
    ctx["agency_client"].patch(
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        data=json.dumps({"default_transfer_id": dest_id}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=_csrf(ctx["agency_client"]),
    )
    disabled = _post(
        ctx["platform"],
        f"/api/v1/platform/transfers/{dest_id}/disable",
        {"confirm": True},
    )
    assert disabled.status_code == 200
    _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": ctx["did"],
            "edge_call_id": "edge-disabled",
            "from_number": "+15550001111",
            "direction": "inbound",
        },
    )
    transfer = _internal(
        "/internal/telephony/v1/voice-session/transfer/",
        {"edge_call_id": "edge-disabled"},
    )
    assert transfer.json()["data"]["reason"] == "disabled"
