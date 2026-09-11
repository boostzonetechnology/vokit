from __future__ import annotations

import json
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.test import Client

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.recordings.domain.policies import object_key
from control_plane.recordings.infrastructure.container import (
    recording_control,
    recording_store,
    tenant_recordings,
)
from control_plane.recordings.models import RecordingAccessGrant
from control_plane.telephony.infrastructure.container import reset_sip_edge
from control_plane.tenancy.infrastructure.container import router, runtime
from shared_kernel.ids import new_uuid7
from tenant.media.service import TenantMediaService

from tests.tenant_db_fixtures import tenant_db_payload

PASSWORD = "Phase2-Demo!ok"
TEL_TOKEN = "test-internal-telephony-token"
REC_TOKEN = "test-internal-recording-token"
CHECKSUM = "sha256:" + ("ab" * 32)
CHECKSUM_OTHER = "sha256:" + ("cd" * 32)


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


def _internal(path: str, payload: dict | None = None, *, token: str = TEL_TOKEN):
    client = Client(enforce_csrf_checks=True)
    return client.post(
        path,
        data=json.dumps(payload or {}),
        content_type="application/json",
        HTTP_X_VOKIT_INTERNAL_TOKEN=token,
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


def _ready_call(*, tag: str, e164: str, hours: list | None = None) -> dict:
    reset_sip_edge()
    _user(f"platform-{tag}@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, f"platform-{tag}@vokit.test")
    agency = _post(
        platform,
        "/api/v1/platform/agencies",
        {
            "display_name": f"Rec {tag}",
            "legal_name": f"Rec {tag}",
            "owner_email": f"oa-{tag}@vokit.test",
            "database": tenant_db_payload(f"oa-{tag}@vokit.test"),
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
        {"display_name": f"Rec Cust {tag}", "agency_id": str(agency_id)},
    )
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    plan = _post(
        platform,
        "/api/v1/platform/plans",
        {
            "name": f"Rec Plan {tag}",
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
    assigned = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/subscription",
        {"plan_version_id": plan.json()["data"]["versions"][0]["id"]},
    )
    assert assigned.status_code == 201
    _user(
        f"agency-{tag}@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=agency_id,
    )
    agency_client = _client()
    _login(agency_client, f"agency-{tag}@vokit.test")
    created = _post(
        agency_client,
        "/api/v1/agency/agents",
        {"customer_id": str(customer_id), "display_name": f"Rec bot {tag}"},
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
                "inbound_enabled": True,
                "greeting": "Hello from Vokit.",
                "voicemail_greeting": "Leave a message.",
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
        {"e164": e164, "country": "US", "monthly_cost_minor": 100},
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
        HTTP_IDEMPOTENCY_KEY=f"rec-did-{tag}",
    )
    assert assigned_number.status_code == 201
    edge_call_id = f"edge-rec-{tag}"
    inbound = _internal(
        "/internal/telephony/v1/voice-session/bootstrap/",
        {
            "did": e164,
            "edge_call_id": edge_call_id,
            "from_number": "+15550001111",
            "direction": "inbound",
        },
    )
    assert inbound.json()["data"]["admitted"] is True
    call_id = uuid.UUID(inbound.json()["data"]["vokit_call_id"])
    ended = _internal(
        "/internal/telephony/v1/voice-session/end/",
        {"edge_call_id": edge_call_id, "reason": "completed", "status": "completed"},
    )
    assert ended.json()["data"]["ok"] is True
    _user(
        f"customer-{tag}@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        tenant_id=agency_id,
        customer_id=customer_id,
    )
    customer_client = _client()
    _login(customer_client, f"customer-{tag}@vokit.test")
    return {
        "platform": platform,
        "agency_client": agency_client,
        "customer_client": customer_client,
        "agency_id": agency_id,
        "customer_id": customer_id,
        "call_id": call_id,
        "edge_call_id": edge_call_id,
        "did": e164,
    }


def _ingest(
    ctx: dict,
    *,
    event_id: str,
    artifact_id: uuid.UUID | None = None,
    put_object: bool = True,
    kind: str = "call_recording",
    checksum: str = CHECKSUM,
    tenant_id: str = "",
) -> object:
    artifact = artifact_id or new_uuid7()
    key = object_key(
        tenant_id=ctx["agency_id"],
        call_id=ctx["call_id"],
        artifact_id=artifact,
    )
    if put_object:
        recording_store().put(object_key=key, checksum=checksum, size_bytes=2048)
    return _internal(
        "/internal/recordings/v1/ingest/",
        {
            "event_id": event_id,
            "edge_call_id": ctx["edge_call_id"],
            "artifact_id": str(artifact),
            "kind": kind,
            "content_type": "audio/wav",
            "size_bytes": 2048,
            "checksum": checksum,
            "tenant_id": tenant_id,
        },
        token=REC_TOKEN,
    ), artifact


@pytest.mark.django_db
def test_recording_negative_matrix() -> None:
    ctx_a = _ready_call(tag="a", e164="+14155550101")
    ingested, artifact_id = _ingest(ctx_a, event_id="evt-a-1")
    assert ingested.status_code == 200
    assert ingested.json()["data"]["status"] == "ready"
    assert ingested.json()["data"]["agency_id"] == str(ctx_a["agency_id"])

    replay = _ingest(ctx_a, event_id="evt-a-1", artifact_id=artifact_id)[0]
    assert replay.json()["data"]["id"] == str(artifact_id)

    conflict = _ingest(
        ctx_a,
        event_id="evt-a-mutate",
        artifact_id=artifact_id,
        put_object=False,
        checksum=CHECKSUM_OTHER,
    )[0]
    assert conflict.status_code == 409

    listed = ctx_a["agency_client"].get(
        f"/api/v1/agency/calls/{ctx_a['call_id']}/artifacts"
    )
    assert listed.status_code == 200
    assert listed.json()["data"][0]["id"] == str(artifact_id)

    access = _post(
        ctx_a["agency_client"],
        f"/api/v1/agency/calls/{ctx_a['call_id']}/artifacts/{artifact_id}/access",
        {},
    )
    assert access.status_code == 200
    token = access.json()["data"]["token"]
    assert access.json()["data"]["url"].endswith(f"token={token}")

    first_use = _internal(
        "/internal/recordings/v1/access/validate/",
        {"token": token},
        token=REC_TOKEN,
    )
    assert first_use.status_code == 200
    replayed = _internal(
        "/internal/recordings/v1/access/validate/",
        {"token": token},
        token=REC_TOKEN,
    )
    assert replayed.status_code == 401
    assert replayed.json()["error"]["code"] == "access_replayed"

    expired_grant = _post(
        ctx_a["agency_client"],
        f"/api/v1/agency/calls/{ctx_a['call_id']}/artifacts/{artifact_id}/access",
        {},
    )
    expired_token = expired_grant.json()["data"]["token"]
    RecordingAccessGrant.objects.filter(artifact_id=artifact_id).update(
        expires_at=datetime.now(UTC) - timedelta(seconds=1)
    )
    expired = _internal(
        "/internal/recordings/v1/access/validate/",
        {"token": expired_token},
        token=REC_TOKEN,
    )
    assert expired.status_code == 401
    assert expired.json()["error"]["code"] == "access_expired"

    anonymous = _client()
    anonymous_denied = _post(
        anonymous,
        f"/api/v1/agency/calls/{ctx_a['call_id']}/artifacts/{artifact_id}/access",
        {},
    )
    assert anonymous_denied.status_code == 401
    missing_route = ctx_a["agency_client"].get(f"/api/v1/artifacts/{artifact_id}")
    assert missing_route.status_code == 404
    wrong_call = _post(
        ctx_a["agency_client"],
        f"/api/v1/agency/calls/{uuid.uuid4()}/artifacts/{artifact_id}/access",
        {},
    )
    assert wrong_call.status_code == 404

    other = _post(
        ctx_a["platform"],
        "/api/v1/platform/customers",
        {"display_name": "Other Cust", "agency_id": str(ctx_a["agency_id"])},
    )
    other_id = uuid.UUID(other.json()["data"]["id"])
    _user(
        "customer-other@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        tenant_id=ctx_a["agency_id"],
        customer_id=other_id,
    )
    other_client = _client()
    _login(other_client, "customer-other@vokit.test")
    foreign_customer = _post(
        other_client,
        f"/api/v1/customer/calls/{ctx_a['call_id']}/artifacts/{artifact_id}/access",
        {},
    )
    assert foreign_customer.status_code == 404

    ctx_b = _ready_call(tag="b", e164="+14155550102")
    forged = _ingest(
        ctx_a,
        event_id="evt-forged",
        tenant_id=str(ctx_b["agency_id"]),
    )[0]
    assert forged.status_code == 200
    assert forged.json()["data"]["agency_id"] == str(ctx_a["agency_id"])
    cross_tenant = _post(
        ctx_b["agency_client"],
        f"/api/v1/agency/calls/{ctx_a['call_id']}/artifacts/{artifact_id}/access",
        {},
    )
    assert cross_tenant.status_code == 404

    too_soon = _post(
        ctx_a["agency_client"],
        f"/api/v1/agency/calls/{ctx_a['call_id']}/artifacts/{artifact_id}/delete",
        {"confirm": True},
    )
    assert too_soon.status_code == 409
    assert too_soon.json()["error"]["details"]["reason"] == "retention"
    held = _post(
        ctx_a["agency_client"],
        f"/api/v1/agency/calls/{ctx_a['call_id']}/artifacts/{artifact_id}/hold",
        {"hold": True},
    )
    assert held.json()["data"]["status"] == "retained"
    hold_blocks = _post(
        ctx_a["agency_client"],
        f"/api/v1/agency/calls/{ctx_a['call_id']}/artifacts/{artifact_id}/delete",
        {"confirm": True},
    )
    assert hold_blocks.json()["error"]["details"]["reason"] == "legal_hold"
    released = _post(
        ctx_a["agency_client"],
        f"/api/v1/agency/calls/{ctx_a['call_id']}/artifacts/{artifact_id}/hold",
        {"hold": False},
    )
    assert released.json()["data"]["status"] == "ready"
    row = tenant_recordings().get_artifact(ctx_a["agency_id"], artifact_id)
    assert row is not None
    tenant_recordings().put_artifact(
        ctx_a["agency_id"],
        replace(row, retention_until=datetime.now(UTC) - timedelta(days=1)),
    )
    deleted = _post(
        ctx_a["agency_client"],
        f"/api/v1/agency/calls/{ctx_a['call_id']}/artifacts/{artifact_id}/delete",
        {"confirm": True},
    )
    assert deleted.json()["data"]["status"] == "deleted"
    after_delete = _post(
        ctx_a["agency_client"],
        f"/api/v1/agency/calls/{ctx_a['call_id']}/artifacts/{artifact_id}/access",
        {},
    )
    assert after_delete.status_code == 404


@pytest.mark.django_db
def test_recording_outage_does_not_corrupt_call_and_orphans_are_visible() -> None:
    ctx = _ready_call(tag="outage", e164="+14155550103")
    artifact_id = new_uuid7()
    recording_store().mark_down()
    down = _ingest(
        ctx, event_id="evt-down", artifact_id=artifact_id, put_object=False
    )[0]
    assert down.status_code == 200
    assert down.json()["data"]["status"] == "verifying"
    listed = ctx["agency_client"].get("/api/v1/agency/calls")
    assert listed.json()["data"][0]["status"] == "completed"
    assert listed.json()["data"][0]["id"] == str(ctx["call_id"])

    recording_store().mark_down(False)
    key = object_key(
        tenant_id=ctx["agency_id"],
        call_id=ctx["call_id"],
        artifact_id=artifact_id,
    )
    recording_store().put(object_key=key, checksum=CHECKSUM, size_bytes=2048)
    recovered = _ingest(ctx, event_id="evt-down", artifact_id=artifact_id)[0]
    assert recovered.json()["data"]["status"] == "ready"

    ghost = new_uuid7()
    recording_store().put(
        object_key=object_key(
            tenant_id=ctx["agency_id"],
            call_id=ctx["call_id"],
            artifact_id=ghost,
        ),
        checksum=CHECKSUM,
        size_bytes=512,
    )
    missing = _ingest(ctx, event_id="evt-orphan-meta", put_object=False)[0]
    assert missing.json()["data"]["status"] == "verifying"
    report = recording_control().reconcile()
    assert any(str(ghost) in key for key in report["orphan_objects"])
    assert missing.json()["data"]["id"] in report["orphan_metadata"]
    output = StringIO()
    call_command("reconcile_recordings", stdout=output)
    text = output.getvalue()
    assert "orphan_objects=" in text
    assert "orphan_metadata=" in text


@pytest.mark.django_db
def test_recording_ingest_rejects_telephony_token_and_fills_voicemail_ref() -> None:
    rejected = _internal(
        "/internal/recordings/v1/ingest/",
        {"event_id": "nope"},
        token=TEL_TOKEN,
    )
    assert rejected.status_code == 401
    tomorrow = (datetime.now(UTC).weekday() + 1) % 7
    ctx = _ready_call(
        tag="vm",
        e164="+14155550104",
        hours=[{"weekday": tomorrow, "start": "09:00", "end": "17:00"}],
    )
    started = _internal(
        "/internal/telephony/v1/voice-session/voicemail/",
        {"edge_call_id": ctx["edge_call_id"], "direction": "inbound", "action": "start"},
    )
    assert started.status_code == 200
    completed = _internal(
        "/internal/telephony/v1/voice-session/voicemail/",
        {
            "edge_call_id": ctx["edge_call_id"],
            "direction": "inbound",
            "action": "complete",
            "duration_seconds": 9,
        },
    )
    assert completed.json()["data"]["object_ref"] == ""
    ingested, artifact_id = _ingest(
        ctx, event_id="evt-vm", kind="voicemail"
    )
    assert ingested.status_code == 200
    rows = [
        row
        for row in ctx["agency_client"].get("/api/v1/agency/calls").json()["data"]
        if row["id"] == str(ctx["call_id"])
    ]
    assert rows
    stored = tenant_recordings().get_artifact(ctx["agency_id"], artifact_id)
    assert stored is not None
    messages = TenantMediaService(router(), runtime()).list_voicemail(
        ctx["agency_id"], call_id=ctx["call_id"]
    )
    assert messages
    assert messages[0].object_ref == stored.object_key


@pytest.mark.django_db
def test_customer_can_grant_access_inside_scope() -> None:
    ctx = _ready_call(tag="cust", e164="+14155550105")
    ingested, artifact_id = _ingest(ctx, event_id="evt-cust")
    assert ingested.status_code == 200
    granted = _post(
        ctx["customer_client"],
        f"/api/v1/customer/calls/{ctx['call_id']}/artifacts/{artifact_id}/access",
        {},
    )
    assert granted.status_code == 200
    assert "token" in granted.json()["data"]
