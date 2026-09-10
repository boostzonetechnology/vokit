from __future__ import annotations

from control_plane.agents.application.ports import GlobalInstructionRepository
from control_plane.agents.domain.policies import InstructionLayers, resolve_instructions
from tenant.agents.domain import TenantAgent
from tenant.agents.service import TenantAgentService


def resolve_for_agent(
    agent: TenantAgent,
    agents: TenantAgentService,
    globals_: GlobalInstructionRepository,
) -> str:
    agency = agents.get_instruction(agent.tenant_id, "agency", agent.tenant_id)
    customer = agents.get_instruction(agent.tenant_id, "customer", agent.customer_id)
    return resolve_instructions(
        InstructionLayers(
            platform_safety=globals_.get(),
            template_base=agent.template_instructions,
            agency=agency.body if agency else "",
            customer=customer.body if customer else "",
            agent=agent.instructions,
        )
    )
