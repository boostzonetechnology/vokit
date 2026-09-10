from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.billing.application.ports import (
    InvoiceIndexRecord,
    InvoiceIndexRepository,
    PlanRepository,
    PlanVersionRecord,
    PlanVersionRepository,
)
from control_plane.billing.domain.policies import assert_invoice_total, line_is_commissionable
from control_plane.billing.domain.types import (
    InvoiceStatus,
    LineKind,
    PlanStatus,
    SubscriptionStatus,
)
from control_plane.customers.application.ports import CustomerIndexRepository
from control_plane.customers.domain.policies import customer_not_found
from control_plane.risk.application.gate import CustomerRiskGate
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from shared_kernel.money import Money
from tenant.billing.domain import InvoiceLineRecord, InvoiceRecord, SubscriptionRecord
from tenant.billing.service import TenantBillingService
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.billing")


@dataclass(frozen=True, slots=True)
class AssignSubscriptionCommand:
    customer_id: uuid.UUID
    plan_version_id: uuid.UUID
    actor_tenant_id: uuid.UUID | None
    privileged: bool


class AssignSubscription:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        plans: PlanRepository,
        versions: PlanVersionRepository,
        invoices: InvoiceIndexRepository,
        billing: TenantBillingService,
        lifecycle: TenantLifecycleService,
        clock: Clock,
        gate: CustomerRiskGate,
    ) -> None:
        self._customers = customers
        self._plans = plans
        self._versions = versions
        self._invoices = invoices
        self._billing = billing
        self._lifecycle = lifecycle
        self._clock = clock
        self._gate = gate

    def execute(self, command: AssignSubscriptionCommand) -> InvoiceRecord:
        customer = self._customers.get(command.customer_id)
        if customer is None:
            raise customer_not_found()
        if not command.privileged:
            if command.actor_tenant_id is None or command.actor_tenant_id != customer.tenant_id:
                raise customer_not_found()
        tenant_customer = self._lifecycle.get_customer(customer.tenant_id, customer.id)
        if tenant_customer is None:
            raise customer_not_found()
        self._gate.assert_open(customer.id)
        version = self._require_version(command.plan_version_id)
        existing = self._billing.get_active_subscription(customer.tenant_id, customer.id)
        if existing is not None:
            raise DomainError(
                "subscription_exists",
                "Customer already has an active subscription.",
                http_status=409,
            )
        now = self._clock.now()
        subscription = SubscriptionRecord(
            subscription_id=new_uuid7(),
            tenant_id=customer.tenant_id,
            customer_id=customer.id,
            plan_id=version.plan_id,
            plan_version_id=version.id,
            status=SubscriptionStatus.ACTIVE,
            cycle="monthly",
            created_at=now,
            updated_at=now,
        )
        invoice = self._open_invoice(subscription, version, now)
        self._billing.put_subscription(customer.tenant_id, subscription)
        stored = self._billing.put_invoice(customer.tenant_id, invoice)
        self._invoices.create(
            InvoiceIndexRecord(
                invoice_id=stored.invoice_id,
                tenant_id=customer.tenant_id,
                customer_id=customer.id,
                status=stored.status,
                total=Money(stored.total_minor, stored.currency),
                created_at=now,
                paid_at=None,
            )
        )
        if version.used_at is None:
            self._versions.update(
                PlanVersionRecord(
                    id=version.id,
                    plan_id=version.plan_id,
                    version=version.version,
                    price=version.price,
                    included_minutes=version.included_minutes,
                    allow_topups=version.allow_topups,
                    topup_minutes=version.topup_minutes,
                    topup_price=version.topup_price,
                    overage_enabled=version.overage_enabled,
                    overage_price_per_minute=version.overage_price_per_minute,
                    grace_seconds=version.grace_seconds,
                    used_at=now,
                    created_at=version.created_at,
                )
            )
        log_event(
            logger,
            "billing.subscription.assigned",
            outcome="success",
            tenant_id=str(customer.tenant_id),
            customer_id=str(customer.id),
            invoice_id=str(stored.invoice_id),
        )
        return stored

    def _require_version(self, version_id: uuid.UUID) -> PlanVersionRecord:
        version = self._versions.get(version_id)
        if version is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        plan = self._plans.get(version.plan_id)
        if plan is None or plan.status is PlanStatus.ARCHIVED:
            raise DomainError("plan_archived", "Plan is not assignable.", http_status=409)
        return version

    def _open_invoice(
        self,
        subscription: SubscriptionRecord,
        version: PlanVersionRecord,
        now,
    ) -> InvoiceRecord:
        line = InvoiceLineRecord(
            line_id=new_uuid7(),
            kind=LineKind.SUBSCRIPTION,
            description="Monthly subscription",
            amount_minor=version.price.minor_units,
            currency=version.price.currency,
            minutes=version.included_minutes,
            commissionable=line_is_commissionable(LineKind.SUBSCRIPTION),
        )
        total = Money(line.amount_minor, line.currency)
        assert_invoice_total((total,), total)
        return InvoiceRecord(
            invoice_id=new_uuid7(),
            tenant_id=subscription.tenant_id,
            customer_id=subscription.customer_id,
            subscription_id=subscription.subscription_id,
            status=InvoiceStatus.OPEN,
            currency=total.currency,
            total_minor=total.minor_units,
            lines=(line,),
            created_at=now,
            updated_at=now,
            paid_at=None,
        )
