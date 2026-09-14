from __future__ import annotations

import json
import uuid
from unittest.mock import patch

import pytest
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.platform_settings.infrastructure.container import platform_settings
from shared_kernel.ids import new_uuid7
from tests.tenant_db_fixtures import platform_customer_body, tenant_db_payload

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


def _patch(client: Client, path: str, payload: dict):
    return client.patch(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=_csrf(client),
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


def _setting(client: Client, key: str, value: object) -> None:
    response = _patch(
        client,
        "/api/v1/platform/settings",
        {"key": key, "value": value, "reason": "voice lab"},
    )
    assert response.status_code == 200, response.content


def _ready_voice_stack():
    _user("platform-voice-set@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform-voice-set@vokit.test")
    agency = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": "Voice Settings A",
            "legal_name": "Voice Settings A",
            "owner_email": "oa-voice-set@vokit.test",
            "database": tenant_db_payload("oa-voice-set@vokit.test"),
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
        platform_customer_body(agency_id, "Voice Set Cust"),
    )
    assert customer.status_code == 201
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    customer_activated = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/status",
        {"action": "activate"},
    )
    assert customer_activated.status_code == 200
    plan = _post(
        platform,
        "/api/v1/platform/plans",
        {
            "name": "Voice Set Plan",
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
        "agency-voice-set@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=agency_id,
    )
    _user(
        "cust-voice-set@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        tenant_id=agency_id,
        customer_id=customer_id,
    )
    agency_client = _client()
    _login(agency_client, "agency-voice-set@vokit.test")
    customer_client = _client()
    _login(customer_client, "cust-voice-set@vokit.test")
    created = _post(
        agency_client,
        "/api/v1/agency/agents",
        {"customer_id": str(customer_id), "display_name": "Voice set bot"},
    )
    agent_id = created.json()["data"]["id"]
    configured = agency_client.patch(
        f"/api/v1/agency/agents/{agent_id}",
        data=json.dumps(
            {
                "voice_provider": "elevenlabs",
                "voice_id": "agent-voice-1",
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
        {"e164": "+14155550888", "country": "US", "monthly_cost_minor": 100},
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
        HTTP_IDEMPOTENCY_KEY="voice-set-did-1",
    )
    assert assigned_number.status_code == 201
    return {
        "platform": platform,
        "agency_client": agency_client,
        "customer_client": customer_client,
        "agent_id": agent_id,
        "did": "+14155550888",
    }


@pytest.mark.django_db
def test_invalid_llm_provider_is_rejected() -> None:
    ctx = _ready_voice_stack()
    response = _patch(
        ctx["platform"],
        "/api/v1/platform/settings",
        {"key": "telephony.llm_provider", "value": "foo", "reason": "bad vendor"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.django_db
def test_voice_api_key_is_encrypted_and_never_returned() -> None:
    ctx = _ready_voice_stack()
    saved = _patch(
        ctx["platform"],
        "/api/v1/platform/settings",
        {"key": "voice.deepgram.api_key", "value": "dg-secret-plain", "reason": "store key"},
    )
    assert saved.status_code == 200
    keys = {item["key"]: item for item in saved.json()["data"]["settings"]}
    assert keys["voice.deepgram.api_key"]["value"] is None
    assert keys["voice.deepgram.api_key"]["has_value"] is True
    assert keys["voice.deepgram.api_key"]["secret"] is True
    blob = json.dumps(saved.json())
    assert "dg-secret-plain" not in blob
    assert platform_settings().decrypted_vendor_key("deepgram") == "dg-secret-plain"
    empty = _patch(
        ctx["platform"],
        "/api/v1/platform/settings",
        {"key": "voice.deepgram.api_key", "value": "", "reason": "clear"},
    )
    assert empty.status_code == 400


@pytest.mark.django_db
def test_bootstrap_uses_platform_tts_not_agent_voice_provider() -> None:
    ctx = _ready_voice_stack()
    _setting(ctx["platform"], "telephony.stt_provider", "cartesia")
    _setting(ctx["platform"], "telephony.tts_provider", "deepgram")
    _setting(ctx["platform"], "telephony.llm_provider", "anthropic")
    _setting(ctx["platform"], "voice.cartesia.api_key", "ck-cartesia")
    _setting(ctx["platform"], "voice.deepgram.api_key", "dg-deepgram")
    _setting(ctx["platform"], "voice.anthropic.api_key", "ak-anthropic")
    bootstrap = _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": ctx["did"],
            "edge_call_id": "edge-voice-set-1",
            "from_number": "+15550001111",
            "sip_call_id": "sip-voice-set",
            "direction": "inbound",
        },
    )
    assert bootstrap.status_code == 200
    providers = bootstrap.json()["data"]["providers"]
    assert providers["stt"]["provider_code"] == "cartesia"
    assert providers["stt"]["api_key"] == "ck-cartesia"
    assert providers["tts"]["provider_code"] == "deepgram"
    assert providers["tts"]["api_key"] == "dg-deepgram"
    assert providers["tts"]["voice_id"] == "agent-voice-1"
    assert providers["llm"]["provider_code"] == "anthropic"
    assert providers["llm"]["api_key"] == "ak-anthropic"


@pytest.mark.django_db
def test_tts_voices_require_active_tts_key_and_are_scoped() -> None:
    ctx = _ready_voice_stack()
    missing = ctx["platform"].get("/api/v1/platform/tts/voices")
    assert missing.status_code == 503
    assert missing.json()["error"]["code"] == "voice_provider_not_configured"
    _setting(ctx["platform"], "telephony.tts_provider", "cartesia")
    no_key = ctx["platform"].get("/api/v1/platform/tts/voices")
    assert no_key.status_code == 503
    assert no_key.json()["error"]["code"] == "secret_missing"
    _setting(ctx["platform"], "voice.cartesia.api_key", "ck-list")
    with patch(
        "control_plane.platform_settings.application.tts_voices.list_tts_voices",
        return_value={
            "provider": "cartesia",
            "voices": [{"id": "voice-a", "name": "Ava", "language": "en"}],
        },
    ) as listed:
        platform_voices = ctx["platform"].get("/api/v1/platform/tts/voices")
        agency_voices = ctx["agency_client"].get("/api/v1/agency/tts/voices")
        customer_voices = ctx["customer_client"].get("/api/v1/customer/tts/voices")
        foreign = ctx["agency_client"].get("/api/v1/platform/tts/voices")
    assert platform_voices.status_code == 200
    assert platform_voices.json()["data"]["provider"] == "cartesia"
    assert platform_voices.json()["data"]["voices"][0]["id"] == "voice-a"
    assert agency_voices.status_code == 200
    assert customer_voices.status_code == 200
    assert foreign.status_code == 403
    assert listed.call_count == 3
    assert listed.call_args.args[0] == "cartesia"
