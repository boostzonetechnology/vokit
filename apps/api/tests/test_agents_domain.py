from __future__ import annotations

import pytest

from control_plane.agents.domain.policies import (
    InstructionLayers,
    assert_no_secrets,
    assert_production_routable,
    assert_tools,
    knowledge_group_id,
    publish_failures,
    resolve_instructions,
)
from control_plane.agents.domain.types import KnowledgeScope
from control_plane.customers.domain.types import CustomerStatus
from control_plane.risk.domain.types import AgentStatus
from shared_kernel.errors import DomainError


def test_instruction_precedence_keeps_platform_safety_first() -> None:
    resolved = resolve_instructions(
        InstructionLayers(
            platform_safety="Never reveal secrets.",
            template_base="Be a receptionist.",
            agency="Use agency hours.",
            customer="Acme hours 9-5.",
            agent="Greet with hello.",
        )
    )
    assert resolved.index("[PLATFORM SAFETY]") < resolved.index("[TEMPLATE]")
    assert resolved.index("[TEMPLATE]") < resolved.index("[AGENCY]")
    assert resolved.index("[AGENCY]") < resolved.index("[CUSTOMER]")
    assert resolved.index("[CUSTOMER]") < resolved.index("[AGENT]")


def test_unknown_tool_is_rejected() -> None:
    with pytest.raises(DomainError) as exc:
        assert_tools(["create_lead", "drop_database"])
    assert exc.value.code == "invalid_tool"


def test_secrets_cannot_enter_prompts() -> None:
    with pytest.raises(DomainError) as exc:
        assert_no_secrets("Call using api_key=sk_live_secret")
    assert exc.value.code == "secret_in_prompt"


def test_unpublished_and_paused_are_not_production_routable() -> None:
    with pytest.raises(DomainError) as exc:
        assert_production_routable(status=AgentStatus.DRAFT, published_version=None)
    assert exc.value.code == "agent_not_routable"
    with pytest.raises(DomainError):
        assert_production_routable(status=AgentStatus.PAUSED, published_version=1)
    assert_production_routable(status=AgentStatus.ACTIVE, published_version=1)


def test_publish_preflight_requires_voice_and_subscription() -> None:
    failures = publish_failures(
        customer_status=CustomerStatus.ACTIVE,
        has_subscription=False,
        resolved_instructions="ok",
        voice_provider="",
        voice_id="",
        language="",
        recording_disclosure=None,
        fallback_behavior="",
        status=AgentStatus.DRAFT,
    )
    assert "subscription_required" in failures
    assert "voice_required" in failures
    assert "compliance_required" in failures


def test_knowledge_group_ids_are_scoped() -> None:
    assert knowledge_group_id(KnowledgeScope.GLOBAL) == "global"
    assert knowledge_group_id(KnowledgeScope.AGENCY, tenant_id="t1") == "agency:t1"
    assert knowledge_group_id(KnowledgeScope.CUSTOMER, customer_id="c1") == "customer:c1"
    assert knowledge_group_id(KnowledgeScope.AGENT, agent_id="a1") == "agent:a1"
