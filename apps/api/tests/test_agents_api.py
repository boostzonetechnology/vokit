from __future__ import annotations

import json
import uuid

import pytest
from django.test import Client

from control_plane.agents.infrastructure.container import vector_store
from control_plane.agents.infrastructure.vectors import HashEmbedding
from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from tests.tenant_db_fixtures import platform_customer_body, tenant_db_payload

PASSWORD = "Phase2-Demo!ok"


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


def _delete(client: Client, path: str):
    return client.delete(path, HTTP_X_CSRFTOKEN=_csrf(client))


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


def _create_agency(client: Client, name: str, db_name: str, owner: str):
    _ = db_name
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
    if response.status_code != 201:
        return response
    agency_id = response.json()["data"]["id"]
    return _post(
        client,
        f"/api/v1/platform/agencies/{agency_id}/status",
        {"action": "activate", "confirm": True},
    )


def _ready_agent():
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "Agent A", "agent_a", "oa-agent@vokit.test")
    assert agency.status_code == 200
    agency_id = uuid.UUID(agency.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        platform_customer_body(agency_id, "Cust Agent"),
    )
    assert customer.status_code == 201
    customer_id = uuid.UUID(customer.json()["data"]["id"])
    activated = _post(
        platform,
        f"/api/v1/platform/customers/{customer_id}/status",
        {"action": "activate", "confirm": True},
    )
    assert activated.status_code == 200
    plan = _post(
        platform,
        "/api/v1/platform/plans",
        {
            "name": "Voice",
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
        platform,
        f"/api/v1/platform/customers/{customer_id}/subscription",
        {"plan_version_id": version_id},
    )
    assert assigned.status_code == 201
    _user(
        "agency-agent@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=agency_id,
    )
    _user(
        "cust-agent@vokit.test",
        PrincipalType.CUSTOMER,
        "customer_owner",
        tenant_id=agency_id,
        customer_id=customer_id,
    )
    agency_client = _client()
    _login(agency_client, "agency-agent@vokit.test")
    customer_client = _client()
    _login(customer_client, "cust-agent@vokit.test")
    created = _post(
        agency_client,
        "/api/v1/agency/agents",
        {"customer_id": str(customer_id), "display_name": "Draft bot"},
    )
    assert created.status_code == 201
    return {
        "platform": platform,
        "agency_id": agency_id,
        "customer_id": customer_id,
        "agency_client": agency_client,
        "customer_client": customer_client,
        "agent_id": created.json()["data"]["id"],
    }


def _publishable(ctx) -> dict:
    return {
        "voice_provider": "elevenlabs",
        "voice_id": "voice-1",
        "language": "en",
        "fallback_behavior": "hangup",
        "recording_disclosure": True,
        "instructions": "Answer briefly.",
        "tools": ["transfer_call"],
        "inbound_enabled": True,
    }


@pytest.mark.django_db
def test_unpublished_agent_is_not_routable() -> None:
    ctx = _ready_agent()
    assert ctx["agency_client"].get(
        f"/api/v1/agency/agents/{ctx['agent_id']}"
    ).json()["data"]["status"] == "draft"
    routing = ctx["agency_client"].get(
        f"/api/v1/agency/agents/{ctx['agent_id']}/routing"
    )
    assert routing.status_code == 200
    assert routing.json()["data"]["routable"] is False
    assert routing.json()["data"]["reason"] == "unpublished"
    denied = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/publish",
        {},
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "publish_preflight_failed"
    configured = _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        _publishable(ctx),
    )
    assert configured.status_code == 200
    published = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/publish",
        {},
    )
    assert published.status_code == 200
    assert published.json()["data"]["status"] == "active"
    assert published.json()["data"]["production_routable"] is True
    assert ctx["agency_client"].get(
        f"/api/v1/agency/agents/{ctx['agent_id']}/routing"
    ).json()["data"]["routable"] is True
    paused = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/pause",
        {},
    )
    assert paused.status_code == 200
    assert paused.json()["data"]["status"] == "paused"
    assert ctx["agency_client"].get(
        f"/api/v1/agency/agents/{ctx['agent_id']}/routing"
    ).json()["data"]["routable"] is False


@pytest.mark.django_db
def test_publish_succeeds_without_agent_voice_provider() -> None:
    ctx = _ready_agent()
    body = _publishable(ctx)
    del body["voice_provider"]
    configured = _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        body,
    )
    assert configured.status_code == 200
    published = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/publish",
        {},
    )
    assert published.status_code == 200
    assert published.json()["data"]["status"] == "active"


@pytest.mark.django_db
def test_template_clone_is_independent() -> None:
    ctx = _ready_agent()
    template = _post(
        ctx["platform"],
        "/api/v1/platform/templates",
        {
            "name": "Receptionist",
            "industry": "dental",
            "use_case": "booking",
            "instructions": "Book appointments.",
            "agent_type": "appointment",
            "voice_provider": "elevenlabs",
            "voice_id": "tpl-voice",
            "language": "en",
            "tools": ["book_appointment"],
            "fallback_behavior": "message",
        },
    )
    assert template.status_code == 201
    installed = _post(
        ctx["agency_client"],
        "/api/v1/agency/agents",
        {
            "customer_id": str(ctx["customer_id"]),
            "template_id": template.json()["data"]["id"],
            "display_name": "From template",
        },
    )
    assert installed.status_code == 201
    assert installed.json()["data"]["status"] == "draft"
    assert installed.json()["data"]["template_instructions"] == "Book appointments."
    _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{installed.json()['data']['id']}",
        {"instructions": "Local only."},
    )
    catalog = ctx["platform"].get("/api/v1/platform/templates")
    assert catalog.json()["data"][0]["name"] == "Receptionist"
    cloned = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{installed.json()['data']['id']}/clone",
        {},
    )
    assert cloned.status_code == 201
    assert cloned.json()["data"]["id"] != installed.json()["data"]["id"]
    assert cloned.json()["data"]["status"] == "draft"


@pytest.mark.django_db
def test_knowledge_isolation_and_test_session_is_not_production() -> None:
    ctx = _ready_agent()
    other = _create_agency(ctx["platform"], "Agent B", "agent_b", "oa-agent-b@vokit.test")
    other_id = uuid.UUID(other.json()["data"]["id"])
    _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        platform_customer_body(other_id, "Other"),
    )
    _user(
        "agency-b@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=other_id,
    )
    other_client = _client()
    _login(other_client, "agency-b@vokit.test")
    source_a = _post(
        ctx["agency_client"],
        "/api/v1/agency/knowledge",
        {"title": "A facts", "body": "Tenant A marker cedar.", "scope": "agency"},
    )
    assert source_a.status_code == 201
    source_b = _post(
        other_client,
        "/api/v1/agency/knowledge",
        {"title": "B facts", "body": "Tenant B marker maple.", "scope": "agency"},
    )
    assert source_b.status_code == 201
    attach = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/knowledge",
        {"source_id": source_a.json()["data"]["id"]},
    )
    assert attach.status_code == 200
    embedding = HashEmbedding()
    hits_a = vector_store().search(
        [source_a.json()["data"]["group_id"]],
        embedding.embed("Tenant A marker cedar."),
    )
    assert any("cedar" in str(hit.get("text")) for hit in hits_a)
    hits_cross = vector_store().search(
        [source_b.json()["data"]["group_id"]],
        embedding.embed("Tenant A marker cedar."),
    )
    assert all("cedar" not in str(hit.get("text")) for hit in hits_cross)
    session = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/test-sessions",
        {"kind": "test", "query": "marker"},
    )
    assert session.status_code == 201
    assert session.json()["data"]["production_routable"] is False
    assert session.json()["data"]["agent_status"] == "testing"
    routing = ctx["agency_client"].get(
        f"/api/v1/agency/agents/{ctx['agent_id']}/routing"
    )
    assert routing.json()["data"]["routable"] is False
    denied_edit = _patch(
        ctx["customer_client"],
        f"/api/v1/customer/agents/{ctx['agent_id']}",
        {"instructions": "customer rewrite"},
    )
    assert denied_edit.status_code == 403


@pytest.mark.django_db
def test_internal_telephony_requires_service_token() -> None:
    response = Client().post("/internal/telephony/v1/voice-session/bootstrap/")
    assert response.status_code == 401


def _publish_ready(ctx) -> dict:
    configured = _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        _publishable(ctx),
    )
    assert configured.status_code == 200
    published = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/publish",
        {},
    )
    assert published.status_code == 200
    return published.json()["data"]


@pytest.mark.django_db
def test_platform_directory_filters_assigned_e164_and_diagnostics() -> None:
    from control_plane.telephony.models import CallIndex, PhoneNumber

    ctx = _ready_agent()
    PhoneNumber.objects.create(
        e164="+15550001111",
        assigned_agent_id=uuid.UUID(ctx["agent_id"]),
        assigned_tenant_id=ctx["agency_id"],
        assigned_customer_id=ctx["customer_id"],
        status="assigned",
    )
    listing = ctx["platform"].get(
        "/api/v1/platform/agents"
        f"?agency_id={ctx['agency_id']}&customer_id={ctx['customer_id']}"
        "&status=draft&agent_type=custom"
    )
    assert listing.status_code == 200
    rows = listing.json()["data"]
    assert len(rows) == 1
    assert rows[0]["id"] == ctx["agent_id"]
    assert rows[0]["assigned_e164"] == "+15550001111"
    assert rows[0]["status_locked"] is False
    detail = ctx["platform"].get(f"/api/v1/platform/agents/{ctx['agent_id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["assigned_e164"] == "+15550001111"
    CallIndex.objects.create(
        id=new_uuid7(),
        tenant_id=ctx["agency_id"],
        customer_id=ctx["customer_id"],
        agent_id=uuid.UUID(ctx["agent_id"]),
        edge_call_id="edge-diag-1",
        e164="+15550001111",
        direction="inbound",
        status="failed",
    )
    diagnostics = ctx["platform"].get(
        f"/api/v1/platform/agents/{ctx['agent_id']}/diagnostics"
    )
    assert diagnostics.status_code == 200
    body = diagnostics.json()["data"]
    assert "runtime" in body
    assert body["runtime"]["production_routable"] is False
    assert any(item.get("kind") == "call" for item in body["errors"])
    assert "recent_calls" in body
    assert "integrations" in body
    missing = ctx["platform"].get(f"/api/v1/platform/agents/{new_uuid7()}")
    assert missing.status_code == 404


@pytest.mark.django_db
def test_sa_status_lock_archive_and_restore() -> None:
    ctx = _ready_agent()
    _publish_ready(ctx)
    paused = _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{ctx['agent_id']}/pause",
        {"reason": "SA pause"},
    )
    assert paused.status_code == 200
    assert paused.json()["data"]["status"] == "paused"
    assert paused.json()["data"]["status_locked"] is True
    routing = ctx["agency_client"].get(
        f"/api/v1/agency/agents/{ctx['agent_id']}/routing"
    )
    assert routing.json()["data"]["routable"] is False
    locked_pause = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/pause",
        {},
    )
    assert locked_pause.status_code == 409
    assert locked_pause.json()["error"]["code"] == "agent_status_locked"
    locked_publish = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/publish",
        {},
    )
    assert locked_publish.status_code == 409
    assert locked_publish.json()["error"]["code"] == "agent_status_locked"
    archived = _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{ctx['agent_id']}/archive",
        {"reason": "retire"},
    )
    assert archived.status_code == 200
    assert archived.json()["data"]["status"] == "archived"
    assert ctx["agency_client"].get(
        f"/api/v1/agency/agents/{ctx['agent_id']}/routing"
    ).json()["data"]["routable"] is False
    blocked_edit = _patch(
        ctx["platform"],
        f"/api/v1/platform/agents/{ctx['agent_id']}",
        {"greeting": "nope"},
    )
    assert blocked_edit.status_code == 409
    restored = _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{ctx['agent_id']}/status",
        {"status": "active"},
    )
    assert restored.status_code == 200
    assert restored.json()["data"]["status"] == "active"
    assert restored.json()["data"]["status_locked"] is False
    agency_pause = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/pause",
        {},
    )
    assert agency_pause.status_code == 200
    assert agency_pause.json()["data"]["status"] == "paused"
    missing_reason = _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{ctx['agent_id']}/disable",
        {},
    )
    assert missing_reason.status_code == 400


@pytest.mark.django_db
def test_chargeback_suspend_stays_locked_from_agency() -> None:
    from control_plane.identity.infrastructure.clock import SystemClock
    from control_plane.risk.infrastructure.container import tenant_agents

    ctx = _ready_agent()
    _publish_ready(ctx)
    tenant_agents().suspend_for_customer(
        ctx["agency_id"], ctx["customer_id"], SystemClock().now()
    )
    detail = ctx["agency_client"].get(f"/api/v1/agency/agents/{ctx['agent_id']}")
    assert detail.json()["data"]["status"] == "suspended"
    assert detail.json()["data"]["status_locked"] is True
    assert detail.json()["data"]["status_actor"] == "system"
    denied = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/pause",
        {},
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "agent_status_locked"
    sa_restore = _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{ctx['agent_id']}/status",
        {"status": "active"},
    )
    assert sa_restore.status_code == 200


@pytest.mark.django_db
def test_platform_clone_is_independent_across_customers() -> None:
    from control_plane.risk.infrastructure.container import tenant_agents

    ctx = _ready_agent()
    _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        {
            "instructions": "Source only.",
            "greeting": "Hello source",
            "voice_id": "voice-1",
            "language": "en",
        },
    )
    source_knowledge = _post(
        ctx["agency_client"],
        "/api/v1/agency/knowledge",
        {"title": "Source facts", "body": "keep on source", "scope": "agency"},
    )
    assert source_knowledge.status_code == 201
    attach = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/knowledge",
        {"source_id": source_knowledge.json()["data"]["id"]},
    )
    assert attach.status_code == 200
    other = _create_agency(ctx["platform"], "Clone B", "clone_b", "oa-clone-b@vokit.test")
    other_id = uuid.UUID(other.json()["data"]["id"])
    other_customer = _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        platform_customer_body(other_id, "Clone Cust"),
    )
    assert other_customer.status_code == 201
    other_customer_id = uuid.UUID(other_customer.json()["data"]["id"])
    cloned = _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{ctx['agent_id']}/clone",
        {
            "customer_id": str(other_customer_id),
            "display_name": "Independent clone",
            "greeting": "Hello clone",
            "system_prompt": "Clone prompt",
        },
    )
    assert cloned.status_code == 201
    body = cloned.json()["data"]
    assert body["id"] != ctx["agent_id"]
    assert body["customer_id"] == str(other_customer_id)
    assert body["agency_id"] == str(other_id)
    assert body["status"] == "draft"
    assert body["instructions"] == "Source only."
    assert body["greeting"] == "Hello clone"
    assert body["template_instructions"] == "Clone prompt"
    assert body["published_version"] is None
    source = ctx["agency_client"].get(f"/api/v1/agency/agents/{ctx['agent_id']}")
    assert source.json()["data"]["greeting"] == "Hello source"
    assert source.json()["data"]["instructions"] == "Source only."
    assert tenant_agents().list_attachments(other_id, uuid.UUID(body["id"])) == []
    assert tenant_agents().list_attachments(
        ctx["agency_id"], uuid.UUID(ctx["agent_id"])
    )
    _patch(
        ctx["platform"],
        f"/api/v1/platform/agents/{body['id']}",
        {"instructions": "Clone rewrite"},
    )
    source_after = ctx["agency_client"].get(f"/api/v1/agency/agents/{ctx['agent_id']}")
    assert source_after.json()["data"]["instructions"] == "Source only."
    agency_clone = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/clone",
        {},
    )
    assert agency_clone.status_code == 201
    assert agency_clone.json()["data"]["customer_id"] == str(ctx["customer_id"])
    other_user = _user(
        "agency-clone-b@vokit.test",
        PrincipalType.AGENCY,
        "agency_owner",
        tenant_id=other_id,
    )
    _ = other_user
    other_client = _client()
    _login(other_client, "agency-clone-b@vokit.test")
    foreign = other_client.get(f"/api/v1/agency/agents/{ctx['agent_id']}")
    assert foreign.status_code == 404


@pytest.mark.django_db
def test_agency_clone_to_own_customer_is_independent() -> None:
    from control_plane.risk.infrastructure.container import tenant_agents

    ctx = _ready_agent()
    transfer_id = str(new_uuid7())
    configured = _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        {
            "instructions": "Source only.",
            "greeting": "Hello source",
            "default_transfer_id": transfer_id,
            "role": "Receptionist",
            "tools": ["create_lead"],
        },
    )
    assert configured.status_code == 200
    source_knowledge = _post(
        ctx["agency_client"],
        "/api/v1/agency/knowledge",
        {"title": "Source facts", "body": "keep on source", "scope": "agency"},
    )
    assert source_knowledge.status_code == 201
    attach = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/knowledge",
        {"source_id": source_knowledge.json()["data"]["id"]},
    )
    assert attach.status_code == 200
    other = _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        platform_customer_body(ctx["agency_id"], "Clone Cust 2"),
    )
    assert other.status_code == 201
    other_customer_id = uuid.UUID(other.json()["data"]["id"])
    activated = _post(
        ctx["platform"],
        f"/api/v1/platform/customers/{other_customer_id}/status",
        {"action": "activate", "confirm": True},
    )
    assert activated.status_code == 200
    cloned = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/clone",
        {"customer_id": str(other_customer_id)},
    )
    assert cloned.status_code == 201
    body = cloned.json()["data"]
    assert body["id"] != ctx["agent_id"]
    assert body["customer_id"] == str(other_customer_id)
    assert body["agency_id"] == str(ctx["agency_id"])
    assert body["status"] == "draft"
    assert body["instructions"] == "Source only."
    assert body["role"] == "Receptionist"
    assert body["default_transfer_id"] is None
    assert body["published_version"] is None
    assert tenant_agents().list_attachments(ctx["agency_id"], uuid.UUID(body["id"])) == []
    assert tenant_agents().list_attachments(
        ctx["agency_id"], uuid.UUID(ctx["agent_id"])
    )
    source = ctx["agency_client"].get(f"/api/v1/agency/agents/{ctx['agent_id']}")
    assert source.json()["data"]["default_transfer_id"] == transfer_id
    rewritten = _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{body['id']}",
        {"instructions": "Clone rewrite", "greeting": "Hello clone"},
    )
    assert rewritten.status_code == 200
    source_after = ctx["agency_client"].get(f"/api/v1/agency/agents/{ctx['agent_id']}")
    assert source_after.json()["data"]["instructions"] == "Source only."
    assert source_after.json()["data"]["greeting"] == "Hello source"


@pytest.mark.django_db
def test_agency_clone_foreign_customer_is_hidden() -> None:
    ctx = _ready_agent()
    other = _create_agency(ctx["platform"], "Clone X", "clone_x", "oa-clone-x@vokit.test")
    other_id = uuid.UUID(other.json()["data"]["id"])
    other_customer = _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        platform_customer_body(other_id, "Foreign Cust"),
    )
    assert other_customer.status_code == 201
    denied = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/clone",
        {"customer_id": other_customer.json()["data"]["id"]},
    )
    assert denied.status_code == 404


@pytest.mark.django_db
def test_builder_persona_timers_and_schema_overrides() -> None:
    ctx = _ready_agent()
    patched = _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        {
            "speaking_style": "warm",
            "speaking_speed": 1.1,
            "role": "Night receptionist",
            "goals": "Book visits.",
            "constraints": "Do not quote prices.",
            "silence_timeout_seconds": 25,
            "max_call_duration_seconds": 900,
            "tools": ["create_lead"],
            "tool_schema_overrides": {
                "create_lead": {
                    "input_schema": {"required": ["name", "email", "phone"]},
                    "timeout_seconds": 10,
                }
            },
        },
    )
    assert patched.status_code == 200
    data = patched.json()["data"]
    assert data["speaking_style"] == "warm"
    assert data["speaking_speed"] == 1.1
    assert data["role"] == "Night receptionist"
    assert data["silence_timeout_seconds"] == 25
    assert data["max_call_duration_seconds"] == 900
    assert "phone" in data["tool_schemas"]["create_lead"]["input_schema"]["required"]
    dropped = _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        {"tool_schema_overrides": {"update_contact": {"input_schema": {"required": []}}}},
    )
    assert dropped.status_code == 400
    too_fast = _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        {"speaking_speed": 9},
    )
    assert too_fast.status_code == 400
    resolved = ctx["agency_client"].get(
        f"/api/v1/agency/agents/{ctx['agent_id']}/resolved-instructions"
    )
    assert "[PERSONA]" in resolved.json()["data"]["resolved"]
    allow_customer = _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        {"customer_can_edit": True},
    )
    assert allow_customer.status_code == 200
    customer_ignored = _patch(
        ctx["customer_client"],
        f"/api/v1/customer/agents/{ctx['agent_id']}",
        {
            "greeting": "Hi from customer",
            "tool_schema_overrides": {"create_lead": {"timeout_seconds": 2}},
            "speaking_style": "robot",
        },
    )
    assert customer_ignored.status_code == 200
    after = ctx["agency_client"].get(f"/api/v1/agency/agents/{ctx['agent_id']}")
    assert after.json()["data"]["greeting"] == "Hi from customer"
    assert after.json()["data"]["speaking_style"] == "warm"
    assert after.json()["data"]["tool_schemas"]["create_lead"]["timeout_seconds"] == 10


@pytest.mark.django_db
def test_customer_layer_instructions_and_knowledge_detach() -> None:
    ctx = _ready_agent()
    saved = _post(
        ctx["agency_client"],
        "/api/v1/agency/instructions",
        {"customer_id": str(ctx["customer_id"]), "body": "Acme hours 9-5."},
    )
    assert saved.status_code == 200
    assert saved.json()["data"]["scope"] == "customer"
    fetched = ctx["agency_client"].get(
        f"/api/v1/agency/instructions?customer_id={ctx['customer_id']}"
    )
    assert fetched.json()["data"]["body"] == "Acme hours 9-5."
    agency_layer = ctx["agency_client"].get("/api/v1/agency/instructions")
    assert agency_layer.json()["data"]["scope"] == "agency"
    other = _create_agency(ctx["platform"], "Inst X", "inst_x", "oa-inst-x@vokit.test")
    other_id = uuid.UUID(other.json()["data"]["id"])
    foreign_customer = _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        platform_customer_body(other_id, "Foreign Inst"),
    )
    hidden = ctx["agency_client"].get(
        f"/api/v1/agency/instructions?customer_id={foreign_customer.json()['data']['id']}"
    )
    assert hidden.status_code == 404
    source = _post(
        ctx["agency_client"],
        "/api/v1/agency/knowledge",
        {"title": "Detach me", "body": "facts", "scope": "agency"},
    )
    assert source.status_code == 201
    source_id = source.json()["data"]["id"]
    attached = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/knowledge",
        {"source_id": source_id},
    )
    assert attached.status_code == 200
    listed = ctx["agency_client"].get(
        f"/api/v1/agency/agents/{ctx['agent_id']}/knowledge"
    )
    assert listed.status_code == 200
    assert listed.json()["data"][0]["source_id"] == source_id
    detached = _delete(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/knowledge/{source_id}",
    )
    assert detached.status_code == 200
    empty = ctx["agency_client"].get(
        f"/api/v1/agency/agents/{ctx['agent_id']}/knowledge"
    )
    assert empty.json()["data"] == []
    still_there = ctx["agency_client"].get("/api/v1/agency/knowledge")
    assert any(row["id"] == source_id for row in still_there.json()["data"])
    missing = _delete(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/knowledge/{source_id}",
    )
    assert missing.status_code == 404
    audit = ctx["platform"].get("/api/v1/platform/audit-events?action=instruction.updated")
    assert audit.status_code == 200
    assert audit.json()["data"]


@pytest.mark.django_db
def test_agency_knowledge_filters_by_customer_id() -> None:
    ctx = _ready_agent()
    other = _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        platform_customer_body(ctx["agency_id"], "Other Cust"),
    )
    other_id = other.json()["data"]["id"]
    agency_src = _post(
        ctx["agency_client"],
        "/api/v1/agency/knowledge",
        {"title": "Agency facts", "body": "agency marker", "scope": "agency"},
    )
    assert agency_src.status_code == 201
    customer_src = _post(
        ctx["agency_client"],
        "/api/v1/agency/knowledge",
        {
            "title": "Customer facts",
            "body": "customer marker",
            "scope": "customer",
            "customer_id": str(ctx["customer_id"]),
        },
    )
    assert customer_src.status_code == 201
    filtered = ctx["agency_client"].get(
        f"/api/v1/agency/knowledge?customer_id={ctx['customer_id']}"
    )
    assert filtered.status_code == 200
    ids = {row["id"] for row in filtered.json()["data"]}
    assert customer_src.json()["data"]["id"] in ids
    assert agency_src.json()["data"]["id"] not in ids
    empty = ctx["agency_client"].get(f"/api/v1/agency/knowledge?customer_id={other_id}")
    assert empty.status_code == 200
    assert empty.json()["data"] == []
    foreign = _create_agency(ctx["platform"], "Know X", "know_x", "oa-know-x@vokit.test")
    foreign_customer = _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        platform_customer_body(foreign.json()["data"]["id"], "Foreign Know"),
    )
    hidden = ctx["agency_client"].get(
        f"/api/v1/agency/knowledge?customer_id={foreign_customer.json()['data']['id']}"
    )
    assert hidden.status_code == 404


def _post_file(client: Client, path: str, fields: dict, upload):
    payload = dict(fields)
    payload["file"] = upload
    return client.post(path, data=payload, HTTP_X_CSRFTOKEN=_csrf(client))


@pytest.mark.django_db
def test_knowledge_ingest_is_ready_only_after_vector_write() -> None:
    from io import BytesIO
    from unittest.mock import patch

    from django.core.files.uploadedfile import SimpleUploadedFile
    from docx import Document

    ctx = _ready_agent()
    markdown = _post_file(
        ctx["agency_client"],
        "/api/v1/agency/knowledge",
        {"title": "Playbook", "scope": "agency"},
        SimpleUploadedFile(
            "playbook.md", b"# Marker cedar\nHours 9-5.", content_type="text/markdown"
        ),
    )
    assert markdown.status_code == 201
    assert markdown.json()["data"]["status"] == "ready"
    assert markdown.json()["data"]["kind"] == "file"
    hits = vector_store().search(
        [markdown.json()["data"]["group_id"]],
        HashEmbedding().embed("Marker cedar"),
    )
    assert any("cedar" in str(hit.get("text")) for hit in hits)

    buffer = BytesIO()
    document = Document()
    document.add_paragraph("Docx marker maple.")
    document.save(buffer)
    docx = _post_file(
        ctx["agency_client"],
        "/api/v1/agency/knowledge",
        {"title": "Policy", "scope": "agency"},
        SimpleUploadedFile(
            "policy.docx",
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
    )
    assert docx.status_code == 201
    assert docx.json()["data"]["status"] == "ready"

    denied_type = _post_file(
        ctx["agency_client"],
        "/api/v1/agency/knowledge",
        {"title": "No", "scope": "agency"},
        SimpleUploadedFile("payload.exe", b"MZ", content_type="application/octet-stream"),
    )
    assert denied_type.status_code == 422

    with patch(
        "control_plane.agents.infrastructure.vectors.MemoryVectorStore.upsert",
        side_effect=DomainError("knowledge_store_unavailable", "Knowledge store write failed."),
    ):
        failed = _post(
            ctx["agency_client"],
            "/api/v1/agency/knowledge",
            {"title": "Broken", "body": "Never ready until vectors persist.", "scope": "agency"},
        )
    assert failed.status_code == 201
    assert failed.json()["data"]["status"] == "failed"
    failed_hits = vector_store().search(
        [failed.json()["data"]["group_id"]],
        HashEmbedding().embed("Never ready until vectors persist."),
    )
    assert all("Never ready" not in str(hit.get("text")) for hit in failed_hits)


@pytest.mark.django_db
def test_knowledge_delete_requires_confirm_and_respects_customer_scope() -> None:
    ctx = _ready_agent()
    source = _post(
        ctx["agency_client"],
        "/api/v1/agency/knowledge",
        {"title": "Shared", "body": "Agency playbook.", "scope": "agency"},
    )
    assert source.status_code == 201
    source_id = source.json()["data"]["id"]
    attached = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/knowledge",
        {"source_id": source_id},
    )
    assert attached.status_code == 200
    blocked = _delete(ctx["agency_client"], f"/api/v1/agency/knowledge/{source_id}")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "knowledge_in_use"
    assert ctx["agent_id"] in blocked.json()["error"]["details"]["attached_agent_ids"]
    impact = ctx["agency_client"].get(f"/api/v1/agency/knowledge/{source_id}")
    assert impact.json()["data"]["attached_count"] == 1
    deleted = _delete(
        ctx["agency_client"],
        f"/api/v1/agency/knowledge/{source_id}?confirm=true",
    )
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True
    gone = ctx["agency_client"].get(f"/api/v1/agency/knowledge/{source_id}")
    assert gone.status_code == 404
    empty = ctx["agency_client"].get(f"/api/v1/agency/agents/{ctx['agent_id']}/knowledge")
    assert empty.json()["data"] == []

    other = _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        platform_customer_body(ctx["agency_id"], "Other customer"),
    )
    other_id = other.json()["data"]["id"]
    foreign_source = _post(
        ctx["agency_client"],
        "/api/v1/agency/knowledge",
        {
            "title": "Other FAQ",
            "body": "Other customer only.",
            "scope": "customer",
            "owner_id": other_id,
        },
    )
    assert foreign_source.status_code == 201
    denied_attach = _post(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}/knowledge",
        {"source_id": foreign_source.json()["data"]["id"]},
    )
    assert denied_attach.status_code == 404


@pytest.mark.django_db
def test_customer_agent_monitor_number_and_pause_resume() -> None:
    from control_plane.risk.infrastructure.container import tenant_agents
    from control_plane.telephony.models import PhoneNumber
    from shared_kernel.time import utc_now

    ctx = _ready_agent()
    PhoneNumber.objects.create(
        e164="+15550002222",
        assigned_agent_id=uuid.UUID(ctx["agent_id"]),
        assigned_tenant_id=ctx["agency_id"],
        assigned_customer_id=ctx["customer_id"],
        status="assigned",
    )
    other = _post(
        ctx["platform"],
        "/api/v1/platform/customers",
        platform_customer_body(ctx["agency_id"], "Other monitor"),
    )
    assert other.status_code == 201
    other_id = uuid.UUID(other.json()["data"]["id"])
    other_agent = _post(
        ctx["agency_client"],
        "/api/v1/agency/agents",
        {"customer_id": str(other_id), "display_name": "Other bot"},
    )
    assert other_agent.status_code == 201
    other_agent_id = other_agent.json()["data"]["id"]

    listing = ctx["customer_client"].get("/api/v1/customer/agents")
    assert listing.status_code == 200
    rows = listing.json()["data"]
    assert [row["id"] for row in rows] == [ctx["agent_id"]]
    row = rows[0]
    assert row["status"] == "draft"
    assert row["assigned_e164"] == "+15550002222"
    assert row["customer_can_edit"] is False
    assert "language" in row
    assert "inbound_enabled" in row
    assert "outbound_enabled" in row
    hidden = ctx["customer_client"].get(f"/api/v1/customer/agents/{other_agent_id}")
    assert hidden.status_code == 404
    detail = ctx["customer_client"].get(f"/api/v1/customer/agents/{ctx['agent_id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["assigned_e164"] == "+15550002222"

    denied_pause = _post(
        ctx["customer_client"],
        f"/api/v1/customer/agents/{ctx['agent_id']}/pause",
        {},
    )
    assert denied_pause.status_code == 403
    denied_resume = _post(
        ctx["customer_client"],
        f"/api/v1/customer/agents/{ctx['agent_id']}/resume",
        {},
    )
    assert denied_resume.status_code == 403

    greeting_before = _publish_ready(ctx)["greeting"]
    allow = _patch(
        ctx["agency_client"],
        f"/api/v1/agency/agents/{ctx['agent_id']}",
        {"customer_can_edit": True},
    )
    assert allow.status_code == 200
    paused = _post(
        ctx["customer_client"],
        f"/api/v1/customer/agents/{ctx['agent_id']}/pause",
        {},
    )
    assert paused.status_code == 200
    paused_body = paused.json()["data"]
    assert paused_body["status"] == "paused"
    assert paused_body["status_actor"] == "customer"
    assert paused_body["status_locked"] is False
    assert paused_body["production_routable"] is False
    assert paused_body["greeting"] == greeting_before
    resumed = _post(
        ctx["customer_client"],
        f"/api/v1/customer/agents/{ctx['agent_id']}/resume",
        {},
    )
    assert resumed.status_code == 200
    assert resumed.json()["data"]["status"] == "active"
    assert resumed.json()["data"]["production_routable"] is True

    platform_pause = _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{ctx['agent_id']}/pause",
        {"reason": "SA pause"},
    )
    assert platform_pause.status_code == 200
    locked = _post(
        ctx["customer_client"],
        f"/api/v1/customer/agents/{ctx['agent_id']}/pause",
        {},
    )
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "agent_status_locked"
    locked_resume = _post(
        ctx["customer_client"],
        f"/api/v1/customer/agents/{ctx['agent_id']}/resume",
        {},
    )
    assert locked_resume.status_code == 409

    restored = _post(
        ctx["platform"],
        f"/api/v1/platform/agents/{ctx['agent_id']}/status",
        {"status": "active", "reason": "restore"},
    )
    assert restored.status_code == 200
    tenant_agents().suspend_for_customer(ctx["agency_id"], ctx["customer_id"], utc_now())
    frozen = _post(
        ctx["customer_client"],
        f"/api/v1/customer/agents/{ctx['agent_id']}/pause",
        {},
    )
    assert frozen.status_code == 409

