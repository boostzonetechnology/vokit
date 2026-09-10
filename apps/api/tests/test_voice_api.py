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


def _internal(path: str, payload: dict | None = None, *, token: str = TOKEN):
    client = Client(enforce_csrf_checks=True)
    headers = {"HTTP_X_VOKIT_INTERNAL_TOKEN": token} if token else {}
    return client.post(
        path,
        data=json.dumps(payload or {}),
        content_type="application/json",
        **headers,
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


def _ready_voice(*, overage: bool = False, grace: int = 30, publish: bool = True):
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Voice A",
            "legal_name": "Voice A",
            "owner_email": "oa-voice@vokit.test",
        },
    )
    assert agency.status_code == 201
    agency_id = uuid.UUID(agency.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Voice Cust", "agency_id": str(agency_id)},
    )
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    plan = _post(
        platform,
        "/api/v1/platform/plans",
        {
            "name": "Voice Plan",
            "price_minor": 10000,
            "included_minutes": 100,
            "allow_topups": False,
            "topup_minutes": 0,
            "topup_price_minor": 0,
            "overage_enabled": overage,
            "overage_price_per_minute_minor": 10,
            "grace_seconds": grace,
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
        "agency-voice@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=agency_id,
    )
    agency_client = _client()
    _login(agency_client, "agency-voice@vokit.test")
    created = _post(
        agency_client,
        "/api/v1/agency/agents",
        {"customer_id": str(customer_id), "display_name": "Voice bot"},
    )
    agent_id = created.json()["data"]["id"]
    if publish:
        configured = agency_client.patch(
            f"/api/v1/agency/agents/{agent_id}",
            data=json.dumps(
                {
                    "voice_provider": "elevenlabs",
                    "voice_id": "voice-1",
                    "language": "en",
                    "fallback_behavior": "hangup",
                    "recording_disclosure": True,
                    "instructions": "Answer briefly.",
                    "tools": ["transfer_call"],
                    "inbound_enabled": True,
                    "greeting": "Hello from Vokit.",
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
        {"e164": "+14155550999", "country": "US", "monthly_cost_minor": 100},
    )
    number_id = stocked.json()["data"]["id"]
    reserved = _post(
        agency_client,
        "/api/v1/agency/phone-numbers/reservations",
        {"number_id": number_id, "agent_id": agent_id},
    )
    assert reserved.status_code == 201
    assigned_number = _post(
        agency_client,
        "/api/v1/agency/phone-numbers/assignments",
        {"reservation_id": reserved.json()["data"]["id"], "confirm": True},
        HTTP_IDEMPOTENCY_KEY="voice-did-1",
    )
    assert assigned_number.status_code == 201
    return {
        "agency_client": agency_client,
        "agent_id": agent_id,
        "did": "+14155550999",
    }


@pytest.mark.django_db
def test_missing_token_is_rejected() -> None:
    response = _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {"did": "+14155550999", "edge_call_id": "edge-1"},
        token="",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_unpublished_agent_is_not_admitted() -> None:
    ctx = _ready_voice(publish=False)
    resolved = _internal(
        "/internal/telephony/v1/did/resolve/",
        {"did": "14155550999"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["data"]["routable"] is False
    bootstrap = _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": ctx["did"],
            "edge_call_id": "edge-unpub",
            "from_number": "+15550001111",
            "sip_call_id": "sip-1",
            "direction": "inbound",
        },
    )
    assert bootstrap.status_code == 200
    assert bootstrap.json()["data"]["admitted"] is False
    assert bootstrap.json()["data"]["reject_reason"] == "unpublished"


@pytest.mark.django_db
def test_pipecat_bootstrap_succeeds_in_lab() -> None:
    ctx = _ready_voice(grace=30)
    resolved = _internal("/internal/telephony/v1/did/resolve/", {"did": "14155550999"})
    assert resolved.status_code == 200
    assert resolved.json()["data"]["routable"] is True
    bootstrap = _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": ctx["did"],
            "edge_call_id": "edge-lab-1",
            "from_number": "+15550001111",
            "sip_call_id": "sip-lab",
            "direction": "inbound",
        },
    )
    assert bootstrap.status_code == 200
    data = bootstrap.json()["data"]
    assert data["admitted"] is True
    assert data["edge_call_id"] == "edge-lab-1"
    assert "api_key=" not in data["agent"]["resolved_system_prompt"]
    assert data["agent"]["welcome_greeting"] == "Hello from Vokit."
    replay = _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": ctx["did"],
            "edge_call_id": "edge-lab-1",
            "from_number": "+15550001111",
            "direction": "inbound",
        },
    )
    assert replay.json()["data"]["vokit_call_id"] == data["vokit_call_id"]
    events = _internal(
        "/internal/telephony/v1/voice-session/events/",
        {"edge_call_id": "edge-lab-1", "event_type": "heartbeat"},
    )
    assert events.json()["data"]["continue_call"] is True
    continued = _internal(
        "/internal/telephony/v1/voice-session/continue/",
        {"edge_call_id": "edge-lab-1", "elapsed_seconds": 31},
    )
    assert continued.json()["data"]["continue_call"] is False
    assert continued.json()["data"]["reason"] == "minutes_exhausted"
    tool = _internal(
        "/internal/telephony/v1/tools/invoke/",
        {"edge_call_id": "edge-lab-1", "tool": "create_lead", "arguments": {}},
    )
    assert tool.json()["data"]["ok"] is False
    assert tool.json()["data"]["error"] == "invalid_tool"
    assert tool.json()["data"]["continue_call"] is True
    ended = _internal(
        "/internal/telephony/v1/voice-session/end/",
        {"edge_call_id": "edge-lab-1", "reason": "completed", "status": "completed"},
    )
    assert ended.json()["data"]["ok"] is True
    assert ended.json()["data"]["billed_minutes"] >= 0


@pytest.mark.django_db
def test_training_bootstrap_uses_session_token() -> None:
    ctx = _ready_voice()
    started = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/test-sessions",
        {"kind": "training"},
    )
    assert started.status_code == 200 or started.status_code == 201
    token = started.json()["data"]["id"]
    bootstrap = _internal(
        "/internal/telephony/v1/training-session/bootstrap/",
        {"session_token": token},
    )
    assert bootstrap.status_code == 200
    assert bootstrap.json()["data"]["admitted"] is True
    propose = _internal(
        "/internal/telephony/v1/training-session/propose/",
        {
            "session_token": token,
            "kind": "instruction",
            "name": "tone",
            "body": "Be brief.",
        },
    )
    assert propose.json()["data"]["ok"] is True
    confirm = _internal(
        "/internal/telephony/v1/training-session/confirm/",
        {"session_token": token},
    )
    assert confirm.json()["data"]["ok"] is True
    ended = _internal(
        "/internal/telephony/v1/training-session/end/",
        {"session_token": token},
    )
    assert ended.json()["data"]["status"] == "ended"
