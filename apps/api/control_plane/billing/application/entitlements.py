from __future__ import annotations

from dataclasses import replace

from control_plane.billing.application.ports import PlanVersionRecord, PlanVersionRepository
from control_plane.billing.domain.entitlements import (
    PENDING_DOWNGRADE,
    assert_agent_cap,
    assert_concurrency_cap,
    assert_extras_fit,
    assert_integration_allowed,
    assert_number_cap,
    assert_recording_allowed,
)
from control_plane.billing.domain.proration import period_end
from control_plane.risk.domain.types import AgentStatus
from control_plane.telephony.domain.call_types import CallStatus
from control_plane.telephony.domain.types import AssignmentStatus
from shared_kernel.time import ensure_utc
from tenant.agents.service import TenantAgentService
from tenant.billing.domain import SubscriptionRecord
from tenant.billing.service import TenantBillingService
from tenant.numbers.service import TenantNumberService


def period_started(subscription: SubscriptionRecord):
    start = subscription.period_started_at or subscription.created_at
    return ensure_utc(start) if start is not None else None


def clear_pending(subscription: SubscriptionRecord, *, now) -> SubscriptionRecord:
    return replace(
        subscription,
        pending_plan_version_id=None,
        pending_kind=None,
        pending_invoice_id=None,
        pending_effective_at=None,
        updated_at=now,
    )


def apply_due_plan_change(
    billing: TenantBillingService,
    versions: PlanVersionRepository,
    subscription: SubscriptionRecord,
    now,
) -> SubscriptionRecord:
    if subscription.pending_kind != PENDING_DOWNGRADE:
        return subscription
    effective = subscription.pending_effective_at
    target_id = subscription.pending_plan_version_id
    if effective is None or target_id is None or ensure_utc(effective) > now:
        return subscription
    target = versions.get(target_id)
    if target is None:
        return clear_pending(subscription, now=now)
    switched = replace(
        subscription,
        plan_id=target.plan_id,
        plan_version_id=target.id,
        period_started_at=effective,
        pending_plan_version_id=None,
        pending_kind=None,
        pending_invoice_id=None,
        pending_effective_at=None,
        updated_at=now,
    )
    billing.put_subscription(subscription.tenant_id, switched)
    if target.used_at is None:
        versions.update(replace(target, used_at=now))
    from control_plane.billing.application.customer_projection import refresh_plan_projection
    from control_plane.customers.infrastructure.container import customer_index

    refresh_plan_projection(
        customer_index(),
        billing,
        switched.tenant_id,
        switched.customer_id,
        switched,
    )
    return switched


def active_agent_count(agents: TenantAgentService, tenant_id, customer_id) -> int:
    return sum(
        1
        for row in agents.list_agents(tenant_id, customer_id)
        if row.status is AgentStatus.ACTIVE
    )


def assigned_number_count(numbers: TenantNumberService, tenant_id, customer_id) -> int:
    return sum(
        1
        for row in numbers.list_assignments(tenant_id, customer_id=customer_id)
        if row.status is AssignmentStatus.ASSIGNED
    )


def live_call_count(index, tenant_id, customer_id) -> int:
    return sum(
        1
        for row in index.list(tenant_id=tenant_id, customer_id=customer_id)
        if row.status in {CallStatus.RINGING, CallStatus.IN_PROGRESS}
    )


def load_version(
    billing: TenantBillingService,
    versions: PlanVersionRepository,
    tenant_id,
    customer_id,
    now,
) -> tuple[SubscriptionRecord, PlanVersionRecord] | None:
    subscription = billing.get_active_subscription(tenant_id, customer_id)
    if subscription is None:
        return None
    subscription = apply_due_plan_change(billing, versions, subscription, now)
    version = versions.get(subscription.plan_version_id)
    if version is None:
        return None
    return subscription, version


def assert_can_create_agent(
    billing: TenantBillingService,
    versions: PlanVersionRepository,
    agents: TenantAgentService,
    tenant_id,
    customer_id,
    now,
) -> None:
    loaded = load_version(billing, versions, tenant_id, customer_id, now)
    if loaded is None:
        return
    _, version = loaded
    assert_agent_cap(
        max_agents=version.max_agents,
        active_count=active_agent_count(agents, tenant_id, customer_id),
    )


def assert_can_activate_agent(
    billing: TenantBillingService,
    versions: PlanVersionRepository,
    agents: TenantAgentService,
    tenant_id,
    customer_id,
    now,
) -> None:
    assert_can_create_agent(billing, versions, agents, tenant_id, customer_id, now)


def assert_can_assign_number(
    billing: TenantBillingService,
    versions: PlanVersionRepository,
    numbers: TenantNumberService,
    tenant_id,
    customer_id,
    now,
) -> None:
    loaded = load_version(billing, versions, tenant_id, customer_id, now)
    if loaded is None:
        return
    _, version = loaded
    assert_number_cap(
        max_phone_numbers=version.max_phone_numbers,
        assigned_count=assigned_number_count(numbers, tenant_id, customer_id),
    )


def assert_can_connect_integration(
    billing: TenantBillingService,
    versions: PlanVersionRepository,
    tenant_id,
    customer_id,
    provider: str,
    now,
) -> None:
    loaded = load_version(billing, versions, tenant_id, customer_id, now)
    if loaded is None:
        return
    _, version = loaded
    assert_integration_allowed(allowed=version.allowed_integrations, provider=provider)


def assert_can_record(
    billing: TenantBillingService,
    versions: PlanVersionRepository,
    tenant_id,
    customer_id,
    now,
) -> None:
    loaded = load_version(billing, versions, tenant_id, customer_id, now)
    if loaded is None:
        return
    _, version = loaded
    assert_recording_allowed(allowed=version.recording_allowed)


def concurrency_denied(
    billing: TenantBillingService,
    versions: PlanVersionRepository,
    index,
    tenant_id,
    customer_id,
    now,
) -> str | None:
    loaded = load_version(billing, versions, tenant_id, customer_id, now)
    if loaded is None:
        return None
    _, version = loaded
    return assert_concurrency_cap(
        max_concurrency=version.max_concurrency,
        live_count=live_call_count(index, tenant_id, customer_id),
    )


def assert_target_fits(
    version: PlanVersionRecord,
    agents: TenantAgentService,
    numbers: TenantNumberService,
    tenant_id,
    customer_id,
) -> None:
    assert_extras_fit(
        max_agents=version.max_agents,
        active_agents=active_agent_count(agents, tenant_id, customer_id),
        max_phone_numbers=version.max_phone_numbers,
        assigned_numbers=assigned_number_count(numbers, tenant_id, customer_id),
    )


def subscription_period_end(subscription: SubscriptionRecord):
    start = period_started(subscription)
    if start is None:
        return None
    return period_end(start)
