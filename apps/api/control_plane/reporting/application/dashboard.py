from __future__ import annotations

import uuid
from datetime import datetime

from control_plane.agents.infrastructure.container import agent_index
from control_plane.billing.domain.lots import LotBalance, remaining_minutes
from control_plane.billing.domain.types import InvoiceStatus
from control_plane.billing.infrastructure.container import (
    invoice_index,
    plan_versions,
    plans,
    tenant_billing,
)
from control_plane.commission.domain.types import LedgerKind, PayoutStatus
from control_plane.commission.domain.wallet import LedgerView, project_wallet
from control_plane.commission.infrastructure.container import ledger, payouts
from control_plane.customers.infrastructure.container import customer_index
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.kyc.domain.types import KycStatus
from control_plane.kyc.infrastructure.container import kyc_cases
from control_plane.notifications.infrastructure.container import notifications
from control_plane.reporting.domain.periods import ReportWindow, in_window
from control_plane.risk.domain.types import AgentStatus
from control_plane.telephony.domain.call_types import CallStatus
from control_plane.telephony.domain.types import NumberStatus
from control_plane.telephony.infrastructure.container import numbers
from control_plane.telephony.infrastructure.repositories import DjangoCallIndexRepository
from control_plane.tenancy.domain.lifecycle import AgencyStatus
from control_plane.tenancy.infrastructure.container import tenant_repo
from shared_kernel.money import V1_CURRENCY


def _card(key: str, label: str, value: object, href: str) -> dict[str, object]:
    return {"key": key, "label": label, "value": value, "href": href}


def _views(rows) -> tuple[LedgerView, ...]:
    return tuple(
        LedgerView(
            id=row.id,
            kind=row.kind,
            amount_minor=row.amount_minor,
            currency=row.currency,
            commission_id=row.commission_id,
            payout_id=row.payout_id,
            earned_at=row.earned_at,
            available_at=row.available_at,
        )
        for row in rows
    )


def _wallet(tenant_id: uuid.UUID, now: datetime):
    return project_wallet(_views(ledger().list_for_tenant(tenant_id)), now)


class DashboardQueries:
    def __init__(self, clock: SystemClock | None = None) -> None:
        self._clock = clock or SystemClock()

    def platform(
        self,
        window: ReportWindow,
        *,
        agency_id: uuid.UUID | None = None,
    ) -> dict[str, object]:
        now = self._clock.now()
        tenants = tenant_repo().list()
        if agency_id is not None:
            tenants = [row for row in tenants if row.id == agency_id]
        tenant_ids = {row.id for row in tenants}
        customers = [
            row
            for row in customer_index().list()
            if not tenant_ids or row.tenant_id in tenant_ids
        ]
        agents = [
            row
            for row in agent_index().list()
            if not tenant_ids or row.tenant_id in tenant_ids
        ]
        phone_rows = numbers().list()
        if agency_id is not None:
            phone_rows = [row for row in phone_rows if row.assigned_tenant_id == agency_id]
        calls = [
            row
            for row in DjangoCallIndexRepository().list()
            if (not tenant_ids or row.tenant_id in tenant_ids)
            and in_window(row.created_at, window)
        ]
        invoices = [
            row
            for row in invoice_index().list()
            if (not tenant_ids or row.tenant_id in tenant_ids)
        ]
        paid = [
            row
            for row in invoices
            if row.status is InvoiceStatus.PAID
            and in_window(row.paid_at or row.created_at, window)
        ]
        entries = [
            row
            for row in ledger().list_all()
            if not tenant_ids or row.tenant_id in tenant_ids
        ]
        earned = [
            row
            for row in entries
            if row.kind is LedgerKind.COMMISSION_EARNED and in_window(row.earned_at, window)
        ]
        wallets = [_wallet(row.id, now) for row in tenants]
        kyc_queue = [
            row
            for row in kyc_cases().list()
            if (not tenant_ids or row.tenant_id in tenant_ids)
            and row.status
            in {
                KycStatus.SUBMITTED,
                KycStatus.UNDER_REVIEW,
                KycStatus.MORE_INFORMATION_REQUIRED,
            }
        ]
        pending_payouts = [
            row
            for row in payouts().list()
            if (not tenant_ids or row.tenant_id in tenant_ids)
            and row.status
            in {PayoutStatus.REQUESTED, PayoutStatus.APPROVED, PayoutStatus.PROCESSING}
        ]
        revenue = sum(row.total.minor_units for row in paid)
        commission_earned = sum(row.amount_minor for row in earned)
        on_hold = sum(bucket.on_hold_minor for bucket in wallets)
        available = sum(bucket.available_minor for bucket in wallets)
        paid_out = sum(bucket.lifetime_paid_minor for bucket in wallets)
        currency = V1_CURRENCY
        return {
            "period": {
                "preset": window.period,
                "timezone": window.timezone,
                "start": window.start.isoformat(),
                "end": window.end.isoformat(),
            },
            "currency": currency,
            "source": "control_plane_projections",
            "kpis": [
                _card("agencies", "Agencies", len(tenants), "/agencies"),
                _card(
                    "active_agencies",
                    "Active agencies",
                    sum(1 for row in tenants if row.agency_status is AgencyStatus.ACTIVE),
                    "/agencies",
                ),
                _card("customers", "Customers", len(customers), "/customers"),
                _card("agents", "Agents", len(agents), "/agents"),
                _card(
                    "numbers",
                    "Phone numbers",
                    sum(1 for row in phone_rows if row.status is NumberStatus.ASSIGNED)
                    if agency_id
                    else len(phone_rows),
                    "/numbers",
                ),
                _card("calls", "Calls", len(calls), "/calls"),
                _card(
                    "minutes",
                    "Billed minutes",
                    sum(row.billed_minutes for row in calls),
                    "/calls",
                ),
                _card("mrr_minor", "Trailing period revenue", revenue, "/invoices"),
                _card("payments_minor", "Captured payments", revenue, "/payments"),
                _card(
                    "commission_liability_minor",
                    "Commission liability",
                    on_hold + available,
                    "/payouts",
                ),
                _card("pending_payouts", "Pending payouts", len(pending_payouts), "/payouts"),
                _card("kyc_queue", "KYC queue", len(kyc_queue), "/kyc"),
            ],
            "financial": {
                "gross_revenue_minor": revenue,
                "estimated_platform_share_minor": max(0, revenue - commission_earned),
                "agency_commission_minor": commission_earned,
                "held_minor": on_hold,
                "available_minor": available,
                "paid_payouts_minor": paid_out,
                "currency": currency,
            },
            "failed_calls": sum(1 for row in calls if row.status is CallStatus.FAILED),
        }

    def agency(self, tenant_id: uuid.UUID, window: ReportWindow) -> dict[str, object]:
        now = self._clock.now()
        customers = customer_index().list(tenant_id=tenant_id)
        agents = agent_index().list(tenant_id=tenant_id)
        phone_rows = numbers().list(tenant_id=tenant_id)
        calls = [
            row
            for row in DjangoCallIndexRepository().list(tenant_id=tenant_id)
            if in_window(row.created_at, window)
        ]
        paid = [
            row
            for row in invoice_index().list(tenant_id=tenant_id)
            if row.status is InvoiceStatus.PAID
            and in_window(row.paid_at or row.created_at, window)
        ]
        wallet = _wallet(tenant_id, now)
        earned = [
            row
            for row in ledger().list_for_tenant(tenant_id)
            if row.kind is LedgerKind.COMMISSION_EARNED and in_window(row.earned_at, window)
        ]
        kyc = kyc_cases().get_for_tenant(tenant_id)
        payout_rows = payouts().list(tenant_id=tenant_id)
        revenue = sum(row.total.minor_units for row in paid)
        return {
            "period": {
                "preset": window.period,
                "timezone": window.timezone,
                "start": window.start.isoformat(),
                "end": window.end.isoformat(),
            },
            "currency": wallet.currency,
            "source": "control_plane_projections",
            "kpis": [
                _card("customers", "Customers", len(customers), "/customers"),
                _card(
                    "active_agents",
                    "Active agents",
                    sum(1 for row in agents if row.status is AgentStatus.ACTIVE),
                    "/agents",
                ),
                _card("numbers", "Numbers", len(phone_rows), "/numbers"),
                _card("calls", "Calls", len(calls), "/calls"),
                _card(
                    "minutes",
                    "Billed minutes",
                    sum(row.billed_minutes for row in calls),
                    "/calls",
                ),
                _card("customer_mrr_minor", "Customer revenue", revenue, "/invoices"),
                _card(
                    "commission_earned_minor",
                    "Commission earned",
                    sum(row.amount_minor for row in earned),
                    "/wallet",
                ),
                _card("held_minor", "Held", wallet.on_hold_minor, "/wallet"),
                _card("available_minor", "Available", wallet.available_minor, "/wallet"),
                _card(
                    "pending_payout_minor",
                    "Pending payout",
                    wallet.withdrawal_pending_minor,
                    "/payouts",
                ),
                _card(
                    "lifetime_paid_minor",
                    "Lifetime paid",
                    wallet.lifetime_paid_minor,
                    "/payouts",
                ),
            ],
            "alerts": {
                "kyc_status": kyc.status.value if kyc else KycStatus.NOT_STARTED.value,
                "open_invoices": sum(
                    1
                    for row in invoice_index().list(tenant_id=tenant_id)
                    if row.status is InvoiceStatus.OPEN
                ),
                "agent_errors": sum(1 for row in agents if row.status is AgentStatus.ERROR),
                "payout_requested": sum(
                    1 for row in payout_rows if row.status is PayoutStatus.REQUESTED
                ),
                "low_available": wallet.available_minor < 1,
            },
        }

    def customer(
        self,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        window: ReportWindow,
        user_id: uuid.UUID,
    ) -> dict[str, object]:
        agents = agent_index().list(tenant_id=tenant_id, customer_id=customer_id)
        calls = [
            row
            for row in DjangoCallIndexRepository().list(
                tenant_id=tenant_id, customer_id=customer_id
            )
            if in_window(row.created_at, window)
        ]
        invoices = invoice_index().list(tenant_id=tenant_id, customer_id=customer_id)
        open_invoices = [row for row in invoices if row.status is InvoiceStatus.OPEN]
        lots = tenant_billing().list_lots(tenant_id, customer_id)
        balances = tuple(
            LotBalance(
                lot_id=str(lot.lot_id),
                kind=lot.kind,
                remaining_minutes=lot.remaining_minutes,
            )
            for lot in lots
        )
        inbox = notifications().inbox_for(user_id)
        unread = [row for row in inbox if row.get("read_at") is None]
        subscription = tenant_billing().get_active_subscription(tenant_id, customer_id)
        plan_label = "none"
        if subscription is not None:
            version = plan_versions().get(subscription.plan_version_id)
            plan = plans().get(version.plan_id) if version else None
            plan_label = plan.name if plan is not None else "assigned"
        return {
            "period": {
                "preset": window.period,
                "timezone": window.timezone,
                "start": window.start.isoformat(),
                "end": window.end.isoformat(),
            },
            "source": "control_plane_projections",
            "kpis": [
                _card("agents", "Agents", len(agents), "/agents"),
                _card("calls", "Calls this period", len(calls), "/calls"),
                _card(
                    "minutes_used",
                    "Minutes used",
                    sum(row.billed_minutes for row in calls),
                    "/usage",
                ),
                _card(
                    "minutes_remaining",
                    "Minutes remaining",
                    remaining_minutes(balances),
                    "/usage",
                ),
                _card(
                    "plan",
                    "Plan",
                    plan_label,
                    "/invoices",
                ),
                _card("open_invoices", "Open invoices", len(open_invoices), "/invoices"),
            ],
            "alerts": {
                "low_minutes": remaining_minutes(balances) < 10,
                "payment_due": bool(open_invoices),
                "agent_offline": any(row.status is AgentStatus.PAUSED for row in agents),
                "unread_notifications": len(unread),
            },
            "recent_calls": [
                {
                    "id": str(row.call_id),
                    "status": row.status.value,
                    "direction": row.direction.value,
                    "billed_minutes": row.billed_minutes,
                }
                for row in calls[:8]
            ],
        }
