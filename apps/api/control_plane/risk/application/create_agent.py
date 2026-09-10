from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.agents.application.index import sync_agent_index
from control_plane.agents.application.ports import AgentIndexRepository
from control_plane.customers.application.ports import CustomerIndexRepository
from control_plane.customers.domain.policies import customer_not_found
from control_plane.risk.application.gate import CustomerRiskGate
from control_plane.risk.domain.types import AgentStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.agents.domain import TenantAgent
from tenant.agents.service import TenantAgentService
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.risk")


@dataclass(frozen=True, slots=True)
class CreateAgentCommand:
    customer_id: uuid.UUID
    display_name: str
    actor_tenant_id: uuid.UUID | None
    privileged: bool


class CreateAgent:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        lifecycle: TenantLifecycleService,
        agents: TenantAgentService,
        gate: CustomerRiskGate,
        clock: Clock,
        index: AgentIndexRepository,
    ) -> None:
        self._customers = customers
        self._lifecycle = lifecycle
        self._agents = agents
        self._gate = gate
        self._clock = clock
        self._index = index

    def execute(self, command: CreateAgentCommand) -> TenantAgent:
        name = command.display_name.strip()
        if not name:
            raise DomainError("validation_error", "display_name is required.")
        customer = self._customers.get(command.customer_id)
        if customer is None:
            raise customer_not_found()
        if not command.privileged:
            if command.actor_tenant_id is None or command.actor_tenant_id != customer.tenant_id:
                raise customer_not_found()
        if self._lifecycle.get_customer(customer.tenant_id, customer.id) is None:
            raise customer_not_found()
        self._gate.assert_open(customer.id)
        now = self._clock.now()
        agent = TenantAgent(
            agent_id=new_uuid7(),
            tenant_id=customer.tenant_id,
            customer_id=customer.id,
            display_name=name[:128],
            status=AgentStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )
        stored = self._agents.put_agent(customer.tenant_id, agent)
        sync_agent_index(self._index, stored)
        log_event(
            logger,
            "agent.created",
            outcome="success",
            tenant_id=str(customer.tenant_id),
            customer_id=str(customer.id),
            agent_id=str(stored.agent_id),
        )
        return stored
