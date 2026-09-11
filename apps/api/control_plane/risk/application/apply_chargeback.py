from __future__ import annotations

import logging
from dataclasses import dataclass

from control_plane.agents.application.index import sync_agent_index
from control_plane.agents.application.ports import AgentIndexRepository
from control_plane.billing.application.ports import InvoiceIndexRepository, NormalizedPaymentEvent
from control_plane.billing.domain.types import PaymentStatus
from control_plane.commission.application.reverse import ReverseCommission, ReverseCommissionCommand
from control_plane.customers.application.ports import (
    BanIndex,
    CustomerIndexRecord,
    CustomerIndexRepository,
)
from control_plane.customers.domain.policies import BanKey
from control_plane.customers.domain.types import CustomerStatus
from control_plane.risk.application.ports import (
    CustomerEmailLookup,
    RiskCaseRecord,
    RiskCaseRepository,
    RiskEventRecord,
    RiskEventRepository,
)
from control_plane.risk.domain.types import SYSTEM_ACTOR_ID, RiskStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.agents.service import TenantAgentService
from tenant.billing.service import TenantBillingService
from tenant.lifecycle.domain import TenantCustomer
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.risk")


@dataclass(frozen=True, slots=True)
class ChargebackResult:
    duplicate: bool
    status: str
    invoice_id: str
    customer_id: str | None
    agents_suspended: int


class ApplyChargeback:
    def __init__(
        self,
        events: RiskEventRepository,
        cases: RiskCaseRepository,
        invoices: InvoiceIndexRepository,
        customers: CustomerIndexRepository,
        bans: BanIndex,
        emails: CustomerEmailLookup,
        lifecycle: TenantLifecycleService,
        agents: TenantAgentService,
        billing: TenantBillingService,
        reverse: ReverseCommission,
        clock: Clock,
        index: AgentIndexRepository,
    ) -> None:
        self._events = events
        self._cases = cases
        self._invoices = invoices
        self._customers = customers
        self._bans = bans
        self._emails = emails
        self._lifecycle = lifecycle
        self._agents = agents
        self._billing = billing
        self._reverse = reverse
        self._clock = clock
        self._index = index

    def execute(self, event: NormalizedPaymentEvent) -> ChargebackResult:
        if not event.event_id.strip():
            raise DomainError("validation_error", "event_id is required.")
        existing = self._events.get(event.processor, event.event_id)
        if existing is not None:
            customer_id = str(existing.customer_id) if existing.customer_id else None
            return ChargebackResult(
                True, "duplicate", str(event.invoice_id), customer_id, 0
            )
        indexed = self._invoices.get(event.invoice_id)
        if indexed is None:
            self._events.create(
                RiskEventRecord(
                    processor=event.processor,
                    event_id=event.event_id,
                    customer_id=None,
                    kind="chargeback",
                    status="rejected",
                )
            )
            raise DomainError("not_found", "Resource not found.", http_status=404)
        customer = self._customers.get(indexed.customer_id)
        if customer is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        now = self._clock.now()
        payment_ids = self._captured_payment_ids(indexed.tenant_id, indexed.invoice_id)
        self._freeze_account(indexed.tenant_id, customer.id, now)
        agents = self._agents.suspend_for_customer(indexed.tenant_id, customer.id, now)
        for agent in agents:
            sync_agent_index(self._index, agent)
        self._ban(customer.id)
        last_payment_id = payment_ids[-1] if payment_ids else None
        for payment_id in payment_ids:
            try:
                self._reverse.execute(
                    ReverseCommissionCommand(
                        payment_id=payment_id,
                        reason="chargeback",
                        actor_id=SYSTEM_ACTOR_ID,
                    )
                )
            except DomainError as exc:
                if exc.code != "not_found":
                    raise
        case = self._cases.get_for_customer(customer.id)
        self._cases.upsert(
            RiskCaseRecord(
                id=case.id if case is not None else new_uuid7(),
                tenant_id=indexed.tenant_id,
                customer_id=customer.id,
                status=RiskStatus.CHARGEBACK_FROZEN,
                last_invoice_id=indexed.invoice_id,
                last_payment_id=last_payment_id,
                last_event_id=event.event_id,
                note="chargeback",
                permanently_banned=True,
                created_at=case.created_at if case is not None else now,
                updated_at=now,
            )
        )
        self._events.create(
            RiskEventRecord(
                processor=event.processor,
                event_id=event.event_id,
                customer_id=customer.id,
                kind="chargeback",
                status="processed",
            )
        )
        log_event(
            logger,
            "risk.chargeback.applied",
            outcome="success",
            tenant_id=str(indexed.tenant_id),
            customer_id=str(customer.id),
            invoice_id=str(indexed.invoice_id),
            agents_suspended=len(agents),
        )
        return ChargebackResult(
            False,
            "processed",
            str(indexed.invoice_id),
            str(customer.id),
            len(agents),
        )

    def _captured_payment_ids(self, tenant_id, invoice_id):
        payments = self._billing.list_payments(tenant_id, invoice_id)
        return [
            row.payment_id
            for row in payments
            if row.status is PaymentStatus.CAPTURED
        ]

    def _freeze_account(self, tenant_id, customer_id, now) -> None:
        current = self._lifecycle.get_customer(tenant_id, customer_id)
        if current is None:
            return
        if current.status is not CustomerStatus.SUSPENDED:
            self._lifecycle.put_customer(
                tenant_id,
                TenantCustomer(
                    customer_id=current.customer_id,
                    tenant_id=current.tenant_id,
                    display_name=current.display_name,
                    status=CustomerStatus.SUSPENDED,
                    legal_name=current.legal_name,
                    owner_email=current.owner_email,
                    phone=current.phone,
                    country=current.country,
                    timezone=current.timezone,
                    created_at=current.created_at,
                    updated_at=now,
                ),
            )
        indexed = self._customers.get(customer_id)
        if indexed is None or indexed.status is CustomerStatus.SUSPENDED:
            return
        self._customers.update(
            CustomerIndexRecord(
                id=indexed.id,
                tenant_id=indexed.tenant_id,
                display_name=indexed.display_name,
                status=CustomerStatus.SUSPENDED,
                created_at=indexed.created_at,
            )
        )

    def _ban(self, customer_id) -> None:
        self._bans.add(BanKey(kind="external_ref", value=str(customer_id)))
        for email in self._emails.emails_for_customer(customer_id):
            self._bans.add(BanKey(kind="email", value=email))
