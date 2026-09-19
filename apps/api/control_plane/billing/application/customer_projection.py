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
    remaining = remaining_minutes(balances)
    before = customers.get(customer_id)
    customers.project(customer_id, remaining_minutes=remaining)
    if before is not None and before.remaining_minutes >= 10 and remaining < 10:
        from control_plane.notifications.application.hooks import billing_notify
        from control_plane.notifications.infrastructure.recipients import (
            recipients_for_scope,
        )

        billing_notify(
            event_type="minutes.low",
            recipients=(
                *recipients_for_scope(customer_id=customer_id),
                *recipients_for_scope(tenant_id=tenant_id),
            ),
            variables={"customer_id": str(customer_id), "remaining": str(remaining)},
            tenant_id=tenant_id,
            customer_id=customer_id,
        )
