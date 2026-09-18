from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, replace

from control_plane.billing.application.entitlements import (
    apply_due_plan_change,
    assert_target_fits,
    clear_pending,
    period_started,
    subscription_period_end,
)
from control_plane.billing.application.ports import (
    InvoiceIndexRecord,
    InvoiceIndexRepository,
    PlanRepository,
    PlanVersionRecord,
    PlanVersionRepository,
)
from control_plane.billing.application.settle_payment import grant_invoice_lots
from control_plane.billing.domain.entitlements import (
    PENDING_DOWNGRADE,
    PENDING_UPGRADE,
    entitlements_tighter,
)
from control_plane.billing.domain.policies import assert_invoice_total, line_is_commissionable
from control_plane.billing.domain.proration import unused_credit_minor, upgrade_due_at
from control_plane.billing.domain.types import InvoiceStatus, LineKind, PlanStatus
from control_plane.customers.application.ports import CustomerIndexRepository
from control_plane.customers.domain.policies import customer_not_found
from control_plane.risk.application.gate import CustomerRiskGate
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from shared_kernel.money import Money
from tenant.agents.service import TenantAgentService
from tenant.billing.domain import InvoiceLineRecord, InvoiceRecord, SubscriptionRecord
from tenant.billing.service import TenantBillingService
from tenant.lifecycle.service import TenantLifecycleService
from tenant.numbers.service import TenantNumberService

logger = logging.getLogger("vokit.billing")


@dataclass(frozen=True, slots=True)
class ChangeSubscriptionCommand:
    customer_id: uuid.UUID
    plan_version_id: uuid.UUID
    actor_tenant_id: uuid.UUID | None
    privileged: bool


@dataclass(frozen=True, slots=True)
class ChangeSubscriptionResult:
    kind: str
    subscription: SubscriptionRecord
    invoice: InvoiceRecord | None = None


class ChangeSubscription:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        plans: PlanRepository,
        versions: PlanVersionRepository,
        invoices: InvoiceIndexRepository,
        billing: TenantBillingService,
        lifecycle: TenantLifecycleService,
        agents: TenantAgentService,
        numbers: TenantNumberService,
        clock: Clock,
        gate: CustomerRiskGate,
    ) -> None:
        self._customers = customers
        self._plans = plans
        self._versions = versions
        self._invoices = invoices
        self._billing = billing
        self._lifecycle = lifecycle
        self._agents = agents
        self._numbers = numbers
        self._clock = clock
        self._gate = gate

    def execute(self, command: ChangeSubscriptionCommand) -> ChangeSubscriptionResult:
        customer = self._customers.get(command.customer_id)
        if customer is None:
            raise customer_not_found()
        if not command.privileged:
            if command.actor_tenant_id is None or command.actor_tenant_id != customer.tenant_id:
                raise customer_not_found()
        if self._lifecycle.get_customer(customer.tenant_id, customer.id) is None:
            raise customer_not_found()
        self._gate.assert_new_commercial(customer.id)
        now = self._clock.now()
        current = self._billing.get_active_subscription(customer.tenant_id, customer.id)
        if current is None:
            raise DomainError(
                "subscription_required",
                "An active subscription is required.",
                http_status=409,
            )
        current = apply_due_plan_change(self._billing, self._versions, current, now)
        current = self._expire_open_upgrade(current, now)
        if (
            current.pending_kind == PENDING_UPGRADE
            and current.pending_invoice_id is not None
        ):
            raise DomainError(
                "subscription_change_pending",
                "An upgrade invoice is already open.",
                http_status=409,
            )
        target = self._require_version(command.plan_version_id)
        if target.id == current.plan_version_id:
            raise DomainError(
                "same_plan_version",
                "Customer is already on this plan version.",
                http_status=409,
            )
        old = self._versions.get(current.plan_version_id)
        if old is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if target.price.minor_units > old.price.minor_units:
            return self._upgrade(current, target, old, now)
        if target.price.minor_units < old.price.minor_units or _tighter(target, old):
            return self._downgrade(current, target, now)
        return self._apply_now(current, target, now, kind="applied")

    def _require_version(self, version_id: uuid.UUID) -> PlanVersionRecord:
        version = self._versions.get(version_id)
        if version is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        plan = self._plans.get(version.plan_id)
        if plan is None or plan.status is PlanStatus.ARCHIVED:
            raise DomainError("plan_archived", "Plan is not assignable.", http_status=409)
        return version

    def _expire_open_upgrade(
        self, subscription: SubscriptionRecord, now
    ) -> SubscriptionRecord:
        if subscription.pending_kind != PENDING_UPGRADE or subscription.pending_invoice_id is None:
            return subscription
        invoice = self._billing.get_invoice(
            subscription.tenant_id, subscription.pending_invoice_id
        )
        if invoice is None or invoice.status is not InvoiceStatus.OPEN:
            return clear_pending(subscription, now=now)
        if invoice.due_at is None or invoice.due_at > now:
            return subscription
        void_open_invoice(self._billing, self._invoices, invoice, now)
        cleared = clear_pending(subscription, now=now)
        self._billing.put_subscription(subscription.tenant_id, cleared)
        return cleared

    def _upgrade(
        self,
        subscription: SubscriptionRecord,
        target: PlanVersionRecord,
        current_version: PlanVersionRecord,
        now,
    ) -> ChangeSubscriptionResult:
        start = period_started(subscription)
        credit = 0
        if start is not None:
            credit = unused_credit_minor(
                price_minor=current_version.price.minor_units,
                period_start=start,
                now=now,
            )
        credit = min(credit, target.price.minor_units)
        charge = max(0, target.price.minor_units - credit)
        due_at = upgrade_due_at(now)
        invoice = self._upgrade_invoice(subscription, target, credit, charge, now, due_at)
        pending = replace(
            subscription,
            pending_plan_version_id=target.id,
            pending_kind=PENDING_UPGRADE,
            pending_invoice_id=invoice.invoice_id,
            pending_effective_at=None,
            updated_at=now,
        )
        self._billing.put_subscription(subscription.tenant_id, pending)
        stored = self._billing.put_invoice(subscription.tenant_id, invoice)
        if charge == 0:
            paid = replace(stored, status=InvoiceStatus.PAID, paid_at=now, updated_at=now)
            self._billing.put_invoice(subscription.tenant_id, paid)
            grant_invoice_lots(self._billing, paid, now)
            switched = self._switch(pending, target, now)
            self._index_invoice(paid, paid_at=now)
            log_event(
                logger,
                "billing.subscription.changed",
                outcome="success",
                tenant_id=str(subscription.tenant_id),
                customer_id=str(subscription.customer_id),
                invoice_id=str(paid.invoice_id),
            )
            return ChangeSubscriptionResult("upgrade", switched, paid)
        self._index_invoice(stored, paid_at=None)
        log_event(
            logger,
            "billing.subscription.changed",
            outcome="success",
            tenant_id=str(subscription.tenant_id),
            customer_id=str(subscription.customer_id),
            invoice_id=str(stored.invoice_id),
        )
        return ChangeSubscriptionResult("upgrade", pending, stored)

    def _downgrade(
        self, subscription: SubscriptionRecord, target: PlanVersionRecord, now
    ) -> ChangeSubscriptionResult:
        assert_target_fits(
            target,
            self._agents,
            self._numbers,
            subscription.tenant_id,
            subscription.customer_id,
        )
        effective = subscription_period_end(subscription)
        if effective is None:
            raise DomainError("validation_error", "Subscription period is missing.")
        if effective <= now:
            return self._apply_now(subscription, target, now, kind="downgrade")
        pending = replace(
            subscription,
            pending_plan_version_id=target.id,
            pending_kind=PENDING_DOWNGRADE,
            pending_invoice_id=None,
            pending_effective_at=effective,
            updated_at=now,
        )
        stored = self._billing.put_subscription(subscription.tenant_id, pending)
        log_event(
            logger,
            "billing.subscription.changed",
            outcome="success",
            tenant_id=str(subscription.tenant_id),
            customer_id=str(subscription.customer_id),
        )
        return ChangeSubscriptionResult("downgrade", stored, None)

    def _apply_now(
        self,
        subscription: SubscriptionRecord,
        target: PlanVersionRecord,
        now,
        *,
        kind: str,
    ) -> ChangeSubscriptionResult:
        if kind == "downgrade":
            assert_target_fits(
                target,
                self._agents,
                self._numbers,
                subscription.tenant_id,
                subscription.customer_id,
            )
        switched = self._switch(subscription, target, now)
        log_event(
            logger,
            "billing.subscription.changed",
            outcome="success",
            tenant_id=str(subscription.tenant_id),
            customer_id=str(subscription.customer_id),
        )
        return ChangeSubscriptionResult(kind, switched, None)

    def _switch(
        self, subscription: SubscriptionRecord, target: PlanVersionRecord, now
    ) -> SubscriptionRecord:
        switched = replace(
            subscription,
            plan_id=target.plan_id,
            plan_version_id=target.id,
            period_started_at=now,
            pending_plan_version_id=None,
            pending_kind=None,
            pending_invoice_id=None,
            pending_effective_at=None,
            updated_at=now,
        )
        stored = self._billing.put_subscription(subscription.tenant_id, switched)
        if target.used_at is None:
            self._versions.update(replace(target, used_at=now))
        return stored

    def _upgrade_invoice(
        self,
        subscription: SubscriptionRecord,
        target: PlanVersionRecord,
        credit: int,
        charge: int,
        now,
        due_at,
    ) -> InvoiceRecord:
        lines = [
            InvoiceLineRecord(
                line_id=new_uuid7(),
                kind=LineKind.SUBSCRIPTION,
                description="Plan upgrade",
                amount_minor=target.price.minor_units,
                currency=target.price.currency,
                minutes=target.included_minutes,
                commissionable=line_is_commissionable(LineKind.SUBSCRIPTION),
            )
        ]
        amounts = [Money(target.price.minor_units, target.price.currency)]
        if credit > 0:
            lines.append(
                InvoiceLineRecord(
                    line_id=new_uuid7(),
                    kind=LineKind.PROMO,
                    description="Unused time credit",
                    amount_minor=-credit,
                    currency=target.price.currency,
                    minutes=0,
                    commissionable=False,
                )
            )
            amounts.append(Money(-credit, target.price.currency))
        total = Money(charge, target.price.currency)
        assert_invoice_total(tuple(amounts), total)
        return InvoiceRecord(
            invoice_id=new_uuid7(),
            tenant_id=subscription.tenant_id,
            customer_id=subscription.customer_id,
            subscription_id=subscription.subscription_id,
            status=InvoiceStatus.OPEN,
            currency=total.currency,
            total_minor=total.minor_units,
            lines=tuple(lines),
            created_at=now,
            updated_at=now,
            paid_at=None,
            due_at=due_at,
        )

    def _index_invoice(self, invoice: InvoiceRecord, *, paid_at) -> None:
        self._invoices.create(
            InvoiceIndexRecord(
                invoice_id=invoice.invoice_id,
                tenant_id=invoice.tenant_id,
                customer_id=invoice.customer_id,
                status=invoice.status,
                total=Money(invoice.total_minor, invoice.currency),
                created_at=invoice.created_at,
                paid_at=paid_at,
            )
        )


def _tighter(new: PlanVersionRecord, old: PlanVersionRecord) -> bool:
    return entitlements_tighter(
        new_max_agents=new.max_agents,
        old_max_agents=old.max_agents,
        new_max_phone_numbers=new.max_phone_numbers,
        old_max_phone_numbers=old.max_phone_numbers,
        new_max_concurrency=new.max_concurrency,
        old_max_concurrency=old.max_concurrency,
        new_recording_allowed=new.recording_allowed,
        old_recording_allowed=old.recording_allowed,
        new_integrations=new.allowed_integrations,
        old_integrations=old.allowed_integrations,
    )


def void_open_invoice(
    billing: TenantBillingService,
    invoices: InvoiceIndexRepository,
    invoice: InvoiceRecord,
    now,
) -> InvoiceRecord:
    voided = replace(
        invoice, status=InvoiceStatus.VOID, updated_at=now, paid_at=None
    )
    billing.put_invoice(invoice.tenant_id, voided)
    invoices.update(
        InvoiceIndexRecord(
            invoice_id=voided.invoice_id,
            tenant_id=voided.tenant_id,
            customer_id=voided.customer_id,
            status=voided.status,
            total=Money(voided.total_minor, voided.currency),
            created_at=voided.created_at,
            paid_at=None,
        )
    )
    log_event(
        logger,
        "billing.invoice.expired",
        outcome="success",
        tenant_id=str(invoice.tenant_id),
        customer_id=str(invoice.customer_id),
        invoice_id=str(invoice.invoice_id),
    )
    return voided
