from __future__ import annotations

import uuid

from control_plane.billing.domain.lots import LotBalance, remaining_minutes
from control_plane.billing.domain.policies import assigned_plan_is_payment_due
from control_plane.customers.application.ports import CustomerIndexRepository
from tenant.billing.domain import SubscriptionRecord
from tenant.billing.service import TenantBillingService


def refresh_plan_projection(
    customers: CustomerIndexRepository,
    billing: TenantBillingService,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    subscription: SubscriptionRecord | None = None,
) -> None:
    current = (
        subscription
        if subscription is not None
        else billing.get_active_subscription(tenant_id, customer_id)
    )
    if current is None:
        customers.project(customer_id, plan_id=None, payment_due=False)
        return
    due = assigned_plan_is_payment_due(
        current.subscription_id,
        billing.list_invoices(tenant_id, customer_id),
    )
    customers.project(customer_id, plan_id=current.plan_id, payment_due=due)


def refresh_minutes_projection(
    customers: CustomerIndexRepository,
    billing: TenantBillingService,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
) -> None:
    lots = billing.list_lots(tenant_id, customer_id)
    balances = tuple(
        LotBalance(
            lot_id=str(lot.lot_id),
            kind=lot.kind,
            remaining_minutes=lot.remaining_minutes,
        )
        for lot in lots
    )
    customers.project(customer_id, remaining_minutes=remaining_minutes(balances))
