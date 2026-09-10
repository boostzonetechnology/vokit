from __future__ import annotations

from control_plane.agents.application.ports import AgentIndexRecord, AgentIndexRepository
from tenant.agents.domain import TenantAgent


def sync_agent_index(index: AgentIndexRepository, agent: TenantAgent) -> None:
    index.upsert(
        AgentIndexRecord(
            id=agent.agent_id,
            tenant_id=agent.tenant_id,
            customer_id=agent.customer_id,
            display_name=agent.display_name,
            status=agent.status,
            agent_type=agent.agent_type,
            published_version=agent.published_version,
            created_at=agent.created_at,
        )
    )
