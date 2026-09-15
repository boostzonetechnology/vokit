from __future__ import annotations

import uuid

from control_plane.agents.application.builder import assert_agent_routable
from control_plane.agents.application.resolve import resolve_for_agent
from control_plane.agents.infrastructure.container import global_instructions, tenant_agents
from control_plane.integrations.domain.types import ConnectionStatus, DeliveryStatus
from control_plane.integrations.infrastructure.container import integration_control
from control_plane.telephony.domain.call_types import CallStatus
from control_plane.telephony.infrastructure.container import voice_control
from shared_kernel.errors import DomainError
from tenant.agents.domain import TenantAgent


def agent_diagnostics(agent: TenantAgent) -> dict[str, object]:
    resolved = resolve_for_agent(agent, tenant_agents(), global_instructions())
    routable = True
    reason = None
    try:
        assert_agent_routable(
            tenant_agents(),
            tenant_id=agent.tenant_id,
            agent_id=agent.agent_id,
            production=True,
        )
    except DomainError as exc:
        if exc.code != "agent_not_routable":
            raise
        routable = False
        reason = exc.details.get("reason")
    calls = voice_control().list_index_calls(
        tenant_id=agent.tenant_id,
        customer_id=agent.customer_id,
        agent_id=agent.agent_id,
    )
    recent = [
        {
            "id": str(row.call_id),
            "status": row.status.value,
            "direction": row.direction.value,
            "billed_minutes": row.billed_minutes,
            "e164": row.e164,
            "remote_e164": row.remote_e164,
        }
        for row in calls[:20]
    ]
    failed_calls = [
        {
            "id": str(row.call_id),
            "kind": "call",
            "status": row.status.value,
            "direction": row.direction.value,
        }
        for row in calls
        if row.status is CallStatus.FAILED
    ]
    connections = []
    integration_errors: list[dict[str, object]] = []
    action_failures: list[dict[str, object]] = []
    try:
        connections = integration_control().list_connections(
            tenant_id=agent.tenant_id,
            customer_id=agent.customer_id,
            actor_customer_id=None,
            privileged=True,
        )
        unusable = {
            ConnectionStatus.DISABLED.value,
            ConnectionStatus.REVOKED.value,
            ConnectionStatus.PENDING.value,
        }
        integration_errors = [
            {
                "id": row["id"],
                "kind": "integration",
                "provider": row.get("provider"),
                "status": row.get("status"),
            }
            for row in connections
            if str(row.get("status") or "") in unusable
        ]
        deliveries = integration_control().list_deliveries(
            tenant_id=agent.tenant_id,
            customer_id=agent.customer_id,
            actor_customer_id=None,
            privileged=True,
        )
        action_failures = [
            {
                "id": row["id"],
                "kind": "agent_action",
                "event_type": row.get("event_type"),
                "status": row.get("status"),
                "object_id": row.get("object_id"),
            }
            for row in deliveries
            if row.get("event_type") == "agent.action.failed"
            or str(row.get("status") or "")
            in {DeliveryStatus.FAILED.value, DeliveryStatus.DEAD.value}
        ]
    except DomainError:
        connections = []
    return {
        "runtime": {
            "resolved_instructions": resolved,
            "production_routable": routable,
            "reason": reason,
        },
        "recent_calls": recent,
        "errors": failed_calls + integration_errors + action_failures[:20],
        "integrations": connections,
    }


def assigned_e164_map(agent_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
    from control_plane.telephony.models import PhoneNumber

    if not agent_ids:
        return {}
    rows = PhoneNumber.objects.filter(assigned_agent_id__in=agent_ids).exclude(e164="")
    mapped: dict[uuid.UUID, str] = {}
    for row in rows:
        if row.assigned_agent_id and row.e164:
            mapped[row.assigned_agent_id] = row.e164
    return mapped
