from __future__ import annotations

from control_plane.billing.application.add_plan_version import (
    AddPlanVersion,
    ArchivePlan,
    UpdatePlanVersion,
)
from control_plane.billing.application.assign_subscription import AssignSubscription
from control_plane.billing.application.create_plan import CreatePlan
from control_plane.billing.application.create_topup import CreateTopUp
from control_plane.billing.application.pay_invoice import PayInvoice
from control_plane.billing.application.settle_payment import SettlePayment
from control_plane.billing.infrastructure.repositories import (
    DjangoBillingIdempotencyRepository,
    DjangoBillingSettingsRepository,
    DjangoInvoiceIndexRepository,
    DjangoPlanRepository,
    DjangoPlanVersionRepository,
    DjangoProcessorEventRepository,
)
from control_plane.customers.infrastructure.container import customer_index
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.tenancy.infrastructure.container import (
    lifecycle,
    router,
    runtime,
    tenant_repo,
)
from providers.billing.braintree import BraintreePaymentAdapter
from providers.billing.stripe import StripePaymentAdapter
from tenant.billing.service import TenantBillingService


def plans() -> DjangoPlanRepository:
    return DjangoPlanRepository()


def plan_versions() -> DjangoPlanVersionRepository:
    return DjangoPlanVersionRepository()


def invoice_index() -> DjangoInvoiceIndexRepository:
    return DjangoInvoiceIndexRepository()


def processor_events() -> DjangoProcessorEventRepository:
    return DjangoProcessorEventRepository()


def billing_settings() -> DjangoBillingSettingsRepository:
    return DjangoBillingSettingsRepository()


def idempotency() -> DjangoBillingIdempotencyRepository:
    return DjangoBillingIdempotencyRepository()


def tenant_billing() -> TenantBillingService:
    return TenantBillingService(router(), runtime())


def create_plan() -> CreatePlan:
    return CreatePlan(plans(), plan_versions(), SystemClock())


def add_plan_version() -> AddPlanVersion:
    return AddPlanVersion(plans(), plan_versions(), SystemClock())


def update_plan_version() -> UpdatePlanVersion:
    return UpdatePlanVersion(plan_versions())


def archive_plan() -> ArchivePlan:
    return ArchivePlan(plans())


def assign_subscription() -> AssignSubscription:
    from control_plane.risk.infrastructure.container import risk_gate

    return AssignSubscription(
        customer_index(),
        plans(),
        plan_versions(),
        invoice_index(),
        tenant_billing(),
        lifecycle(),
        SystemClock(),
        risk_gate(),
    )


def create_topup() -> CreateTopUp:
    from control_plane.risk.infrastructure.container import risk_gate

    return CreateTopUp(
        plan_versions(),
        invoice_index(),
        idempotency(),
        tenant_billing(),
        SystemClock(),
        risk_gate(),
    )


def pay_invoice() -> PayInvoice:
    from control_plane.risk.infrastructure.container import risk_gate

    return PayInvoice(idempotency(), tenant_billing(), risk_gate())


def settle_payment() -> SettlePayment:
    from control_plane.commission.application.accrue import AccrueCommission
    from control_plane.commission.infrastructure.repositories import (
        DjangoLedgerRepository,
    )

    return SettlePayment(
        processor_events(),
        invoice_index(),
        tenant_billing(),
        SystemClock(),
        AccrueCommission(DjangoLedgerRepository(), tenant_repo()),
    )


def payment_processor(slug: str) -> StripePaymentAdapter | BraintreePaymentAdapter:
    if slug == "stripe":
        return StripePaymentAdapter()
    if slug == "braintree":
        return BraintreePaymentAdapter()
    from shared_kernel.errors import DomainError

    raise DomainError("not_found", "Resource not found.", http_status=404)
