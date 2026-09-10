from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from control_plane.billing.domain.types import InvoiceStatus, LineKind, PaymentStatus
from control_plane.commission.application.accrue import AccrueCommand, AccrueCommission
from control_plane.commission.application.ports import LedgerEntryRecord
from control_plane.commission.application.reverse import ReverseCommission, ReverseCommissionCommand
from control_plane.commission.domain.policies import commission_amount, eligible_base_from_lines
from control_plane.commission.domain.types import LedgerKind
from control_plane.commission.domain.wallet import LedgerView, project_wallet
from control_plane.tenancy.application.ports import TenantRecord
from control_plane.tenancy.domain.lifecycle import AgencyCapabilities, AgencyStatus
from control_plane.tenancy.domain.types import TenantStatus
from shared_kernel.ids import new_uuid7
from shared_kernel.money import Money
from tenant.billing.domain import InvoiceLineRecord, InvoiceRecord, PaymentRecord

SEP1 = datetime(2026, 9, 1, tzinfo=UTC)
SEP5 = datetime(2026, 9, 5, tzinfo=UTC)
SEP9 = datetime(2026, 9, 9, tzinfo=UTC)
SEP10 = datetime(2026, 9, 10, tzinfo=UTC)
HOLD = timedelta(days=15)


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, now: datetime) -> None:
        self._now = now


class FakeTenants:
    def __init__(self, tenant_id: uuid.UUID, rate_bps: int) -> None:
        self.tenant_id = tenant_id
        self.rate_bps = rate_bps

    def get(self, tenant_id: uuid.UUID) -> TenantRecord:
        return TenantRecord(
            id=self.tenant_id,
            display_name="Agency",
            status=TenantStatus.READY,
            agency_status=AgencyStatus.ACTIVE,
            commission_rate_bps=self.rate_bps,
            capabilities=AgencyCapabilities(),
        )

    def list(self) -> list[TenantRecord]:
        return [self.get(self.tenant_id)]


class MemoryLedger:
    def __init__(self) -> None:
        self.rows: list[LedgerEntryRecord] = []

    def append(self, entry: LedgerEntryRecord) -> None:
        self.rows.append(entry)

    def list_for_tenant(self, tenant_id: uuid.UUID) -> list[LedgerEntryRecord]:
        return [row for row in self.rows if row.tenant_id == tenant_id]

    def get(self, entry_id: uuid.UUID) -> LedgerEntryRecord | None:
        return next((row for row in self.rows if row.id == entry_id), None)

    def get_earned_by_payment(self, payment_id: uuid.UUID) -> LedgerEntryRecord | None:
        for row in self.rows:
            if row.kind is LedgerKind.COMMISSION_EARNED and row.payment_id == payment_id:
                return row
        return None

    def has_hold_release(self, commission_id: uuid.UUID) -> bool:
        return any(
            row.kind is LedgerKind.HOLD_RELEASED and row.commission_id == commission_id
            for row in self.rows
        )

    def lock_tenant(self, tenant_id: uuid.UUID) -> None:
        return None


def _views(rows: list[LedgerEntryRecord]) -> tuple[LedgerView, ...]:
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


def _invoice(tenant_id: uuid.UUID, customer_id: uuid.UUID, amount: int) -> InvoiceRecord:
    line = InvoiceLineRecord(
        line_id=new_uuid7(),
        kind=LineKind.SUBSCRIPTION,
        description="Monthly subscription",
        amount_minor=amount,
        currency="USD",
        minutes=100,
        commissionable=True,
    )
    return InvoiceRecord(
        invoice_id=new_uuid7(),
        tenant_id=tenant_id,
        customer_id=customer_id,
        subscription_id=new_uuid7(),
        status=InvoiceStatus.PAID,
        currency="USD",
        total_minor=amount,
        lines=(line,),
    )


def _payment(invoice: InvoiceRecord, amount: int) -> PaymentRecord:
    return PaymentRecord(
        payment_id=new_uuid7(),
        invoice_id=invoice.invoice_id,
        tenant_id=invoice.tenant_id,
        customer_id=invoice.customer_id,
        processor="stripe",
        processor_event_id=str(new_uuid7()),
        amount_minor=amount,
        currency="USD",
        status=PaymentStatus.CAPTURED,
    )


def _accrue(rate_bps: int, amount: int, when: datetime) -> tuple[MemoryLedger, LedgerEntryRecord]:
    tenant_id = new_uuid7()
    customer_id = new_uuid7()
    ledger = MemoryLedger()
    invoice = _invoice(tenant_id, customer_id, amount)
    payment = _payment(invoice, amount)
    entry = AccrueCommission(ledger, FakeTenants(tenant_id, rate_bps)).execute(
        AccrueCommand(payment=payment, invoice=invoice, settled_at=when)
    )
    assert entry is not None
    return ledger, entry


def test_eligible_base_excludes_tax_and_ignores_processor_fees() -> None:
    base = eligible_base_from_lines(
        (
            (LineKind.SUBSCRIPTION, 10000, "USD", True),
            (LineKind.TAX, 800, "USD", False),
        )
    )
    assert base == Money(10000)
    assert commission_amount(base, 3000) == Money(3000)


def test_appendix_c_example_1_normal_subscription() -> None:
    ledger, entry = _accrue(3000, 10000, SEP1)
    assert entry.amount_minor == 3000
    assert entry.eligible_base_minor == 10000
    assert entry.rate_bps_snapshot == 3000
    assert entry.available_at == SEP1 + HOLD
    held = project_wallet(_views(ledger.rows), SEP1 + timedelta(days=1))
    assert held.on_hold_minor == 3000
    assert held.available_minor == 0
    ready = project_wallet(_views(ledger.rows), SEP1 + HOLD)
    assert ready.on_hold_minor == 0
    assert ready.available_minor == 3000
    ledger.append(
        LedgerEntryRecord(
            id=new_uuid7(),
            tenant_id=entry.tenant_id,
            customer_id=None,
            kind=LedgerKind.PAYOUT_RESERVED,
            amount_minor=2000,
            currency="USD",
            payment_id=None,
            invoice_id=None,
            commission_id=None,
            payout_id=new_uuid7(),
            eligible_base_minor=None,
            rate_bps_snapshot=None,
            earned_at=SEP1 + HOLD,
            available_at=SEP1 + HOLD,
            reason="payout_reserved",
            actor_id=None,
        )
    )
    reserved = project_wallet(_views(ledger.rows), SEP1 + HOLD)
    assert reserved.available_minor == 1000
    assert reserved.withdrawal_pending_minor == 2000


def test_appendix_c_example_2_independent_holds() -> None:
    first = _accrue(3000, 10000, SEP1)[0]
    second = _accrue(3000, 15000, SEP5)[0]
    third = _accrue(3000, 6667, SEP10)[0]
    rows = first.rows + second.rows + third.rows
    # Merge onto one tenant for the projection story.
    tenant_id = first.rows[0].tenant_id
    merged = [replace(row, tenant_id=tenant_id) for row in rows]
    mid = project_wallet(_views(merged), datetime(2026, 9, 17, tzinfo=UTC))
    assert mid.available_minor == 3000
    assert mid.on_hold_minor == 4500 + 2000
    late = project_wallet(_views(merged), datetime(2026, 9, 25, tzinfo=UTC))
    assert late.available_minor == 3000 + 4500 + 2000
    assert late.on_hold_minor == 0


def test_appendix_c_example_3_refund_during_hold() -> None:
    ledger, entry = _accrue(3000, 10000, SEP1)
    ReverseCommission(ledger, FakeClock(SEP1 + timedelta(days=2))).execute(
        ReverseCommissionCommand(
            payment_id=entry.payment_id or new_uuid7(),
            reason="full_refund",
            actor_id=new_uuid7(),
        )
    )
    after = project_wallet(_views(ledger.rows), SEP1 + HOLD)
    assert after.on_hold_minor == 0
    assert after.available_minor == 0


def test_appendix_c_example_4_chargeback_after_payout() -> None:
    ledger, entry = _accrue(3000, 10000, SEP1)
    payout_id = new_uuid7()
    paid_at = SEP1 + HOLD + timedelta(days=1)
    ledger.append(
        LedgerEntryRecord(
            id=new_uuid7(),
            tenant_id=entry.tenant_id,
            customer_id=None,
            kind=LedgerKind.PAYOUT_RESERVED,
            amount_minor=3000,
            currency="USD",
            payment_id=None,
            invoice_id=None,
            commission_id=None,
            payout_id=payout_id,
            eligible_base_minor=None,
            rate_bps_snapshot=None,
            earned_at=paid_at,
            available_at=paid_at,
            reason="payout_reserved",
            actor_id=None,
        )
    )
    ledger.append(
        LedgerEntryRecord(
            id=new_uuid7(),
            tenant_id=entry.tenant_id,
            customer_id=None,
            kind=LedgerKind.PAYOUT_PAID,
            amount_minor=3000,
            currency="USD",
            payment_id=None,
            invoice_id=None,
            commission_id=None,
            payout_id=payout_id,
            eligible_base_minor=None,
            rate_bps_snapshot=None,
            earned_at=paid_at,
            available_at=paid_at,
            reason="payout_paid",
            actor_id=None,
        )
    )
    ReverseCommission(ledger, FakeClock(paid_at + timedelta(days=3))).execute(
        ReverseCommissionCommand(
            payment_id=entry.payment_id or new_uuid7(),
            reason="chargeback",
            actor_id=new_uuid7(),
        )
    )
    buckets = project_wallet(_views(ledger.rows), paid_at + timedelta(days=3))
    assert buckets.available_minor == -3000
    assert buckets.lifetime_paid_minor == 3000
    assert buckets.withdrawal_pending_minor == 0


def test_appendix_c_example_5_rate_change_snapshot() -> None:
    tenant_id = new_uuid7()
    customer_id = new_uuid7()
    tenants = FakeTenants(tenant_id, 2000)
    ledger = MemoryLedger()
    accrue = AccrueCommission(ledger, tenants)
    first_invoice = _invoice(tenant_id, customer_id, 10000)
    first = accrue.execute(
        AccrueCommand(
            payment=_payment(first_invoice, 10000),
            invoice=first_invoice,
            settled_at=SEP9,
        )
    )
    tenants.rate_bps = 3000
    second_invoice = _invoice(tenant_id, customer_id, 10000)
    second = accrue.execute(
        AccrueCommand(
            payment=_payment(second_invoice, 10000),
            invoice=second_invoice,
            settled_at=SEP10,
        )
    )
    assert first is not None and second is not None
    assert first.rate_bps_snapshot == 2000
    assert first.amount_minor == 2000
    assert second.rate_bps_snapshot == 3000
    assert second.amount_minor == 3000
    assert first.rate_bps_snapshot != second.rate_bps_snapshot
