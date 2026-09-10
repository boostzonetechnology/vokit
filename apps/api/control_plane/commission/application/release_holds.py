from __future__ import annotations

import logging

from control_plane.commission.application.ports import LedgerEntryRecord, LedgerRepository
from control_plane.commission.domain.types import LedgerKind
from control_plane.tenancy.application.ports import Clock, TenantRepository
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.commission")


class ReleaseHolds:
    def __init__(
        self,
        ledger: LedgerRepository,
        tenants: TenantRepository,
        clock: Clock,
    ) -> None:
        self._ledger = ledger
        self._tenants = tenants
        self._clock = clock

    def execute(self) -> int:
        now = self._clock.now()
        released = 0
        for tenant in self._tenants.list():
            for row in self._ledger.list_for_tenant(tenant.id):
                if row.kind is not LedgerKind.COMMISSION_EARNED:
                    continue
                if row.available_at is None or now < row.available_at:
                    continue
                if self._ledger.has_hold_release(row.id):
                    continue
                self._ledger.append(
                    LedgerEntryRecord(
                        id=new_uuid7(),
                        tenant_id=row.tenant_id,
                        customer_id=row.customer_id,
                        kind=LedgerKind.HOLD_RELEASED,
                        amount_minor=0,
                        currency=row.currency,
                        payment_id=row.payment_id,
                        invoice_id=row.invoice_id,
                        commission_id=row.id,
                        payout_id=None,
                        eligible_base_minor=None,
                        rate_bps_snapshot=None,
                        earned_at=row.earned_at,
                        available_at=row.available_at,
                        reason="hold_elapsed",
                        actor_id=None,
                        created_at=now,
                    )
                )
                released += 1
        if released:
            log_event(
                logger,
                "commission.holds.released",
                outcome="success",
                count=released,
            )
        return released
