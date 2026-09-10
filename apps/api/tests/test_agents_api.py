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
from shared_kernel.ids import new_uuid7

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
    return _post(
        client,
        "/api/v1/platform/agencies",
        {
            "display_name": name,
            "legal_name": name,
            "owner_email": owner,
        },
    )


def _ready_agent():
    _user("platform@vokit.test", PrincipalType.PLATFORM, "super_admin")
    platform = _client()
    _login(platform, "platform@vokit.test")
    agency = _create_agency(platform, "Agent A", "agent_a", "oa-agent@vokit.test")
    assert agency.status_code == 201
    agency_id = uuid.UUID(agency.json()["data"]["id"])
    customer = _post(
        platform,
        "/api/v1/platform/customers",
        {"display_name": "Cust Agent", "agency_id": str(agency_id)},
    )
    customer_id = uuid.UUID(customer.json()["data"]["id"])
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
        {"display_name": "Other", "agency_id": str(other_id)},
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
