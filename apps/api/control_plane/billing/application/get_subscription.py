from __future__ import annotations

import uuid
from dataclasses import dataclass

from control_plane.billing.application.ports import PlanRepository, PlanVersionRepository
from control_plane.customers.application.ports import CustomerIndexRepository
from control_plane.customers.domain.policies import customer_not_found
from shared_kernel.errors import DomainError
from tenant.billing.domain import SubscriptionRecord
from tenant.billing.service import TenantBillingService


@dataclass(frozen=True, slots=True)
class CustomerSubscriptionView:
    subscription: SubscriptionRecord
    plan_name: str
    plan_version: int
    included_minutes: int


class GetCustomerSubscription:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        billing: TenantBillingService,
        plans: PlanRepository,
        versions: PlanVersionRepository,
    ) -> None:
        self._customers = customers
        self._billing = billing
        self._plans = plans
        self._versions = versions

    def execute(self, customer_id: uuid.UUID) -> CustomerSubscriptionView | None:
        indexed = self._customers.get(customer_id)
        if indexed is None:
            raise customer_not_found()
        subscription = self._billing.get_active_subscription(
            indexed.tenant_id, customer_id
        )
        if subscription is None:
            return None
        version = self._versions.get(subscription.plan_version_id)
        if version is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        plan = self._plans.get(subscription.plan_id)
        return CustomerSubscriptionView(
            subscription=subscription,
            plan_name=plan.name if plan else "",
            plan_version=version.version,
            included_minutes=version.included_minutes,
        )
