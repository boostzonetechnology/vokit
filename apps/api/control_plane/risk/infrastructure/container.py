from __future__ import annotations

from control_plane.billing.infrastructure.repositories import DjangoInvoiceIndexRepository
from control_plane.commission.application.reverse import ReverseCommission
from control_plane.commission.infrastructure.repositories import DjangoLedgerRepository
from control_plane.customers.infrastructure.container import ban_index, customer_index
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.risk.application.apply_chargeback import ApplyChargeback
from control_plane.risk.application.create_agent import CreateAgent
from control_plane.risk.application.flag_risk import FlagRiskyPayment
from control_plane.risk.application.gate import CustomerRiskGate
from control_plane.risk.application.override import OverrideRisk
from control_plane.risk.application.submit_verification import SubmitVerification
from control_plane.risk.infrastructure.repositories import (
    DjangoCustomerEmailLookup,
    DjangoRiskCaseRepository,
    DjangoRiskEventRepository,
    DjangoVerificationRepository,
)
from control_plane.tenancy.infrastructure.container import lifecycle, router, runtime
from tenant.agents.service import TenantAgentService
from tenant.billing.service import TenantBillingService


def risk_cases() -> DjangoRiskCaseRepository:
    return DjangoRiskCaseRepository()


def risk_events() -> DjangoRiskEventRepository:
    return DjangoRiskEventRepository()


def verifications() -> DjangoVerificationRepository:
    return DjangoVerificationRepository()


def risk_gate() -> CustomerRiskGate:
    return CustomerRiskGate(risk_cases())


def tenant_agents() -> TenantAgentService:
    return TenantAgentService(router(), runtime())


def tenant_billing() -> TenantBillingService:
    return TenantBillingService(router(), runtime())


def apply_chargeback() -> ApplyChargeback:
    from control_plane.agents.infrastructure.repositories import DjangoAgentIndexRepository

    return ApplyChargeback(
        risk_events(),
        risk_cases(),
        DjangoInvoiceIndexRepository(),
        customer_index(),
        ban_index(),
        DjangoCustomerEmailLookup(),
        lifecycle(),
        tenant_agents(),
        tenant_billing(),
        ReverseCommission(DjangoLedgerRepository(), SystemClock()),
        SystemClock(),
        DjangoAgentIndexRepository(),
    )


def flag_risky_payment() -> FlagRiskyPayment:
    return FlagRiskyPayment(
        risk_events(),
        risk_cases(),
        DjangoInvoiceIndexRepository(),
        SystemClock(),
    )


def submit_verification() -> SubmitVerification:
    return SubmitVerification(
        customer_index(),
        risk_cases(),
        verifications(),
        SystemClock(),
    )


def override_risk() -> OverrideRisk:
    return OverrideRisk(risk_cases(), SystemClock())


def create_agent() -> CreateAgent:
    from control_plane.agents.infrastructure.repositories import DjangoAgentIndexRepository
    from control_plane.tenancy.infrastructure.container import tenant_repo

    return CreateAgent(
        customer_index(),
        lifecycle(),
        tenant_agents(),
        risk_gate(),
        SystemClock(),
        DjangoAgentIndexRepository(),
        tenant_repo(),
    )
