from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.commission.application.ports import LedgerEntryRecord, LedgerRepository
from control_plane.commission.domain.types import LedgerKind
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.commission")


@dataclass(frozen=True, slots=True)
class ReverseCommissionCommand:
    payment_id: uuid.UUID
    reason: str
    actor_id: uuid.UUID


class ReverseCommission:
    def __init__(self, ledger: LedgerRepository, clock: Clock) -> None:
        self._ledger = ledger
        self._clock = clock

    def execute(self, command: ReverseCommissionCommand) -> LedgerEntryRecord:
        earned = self._ledger.get_earned_by_payment(command.payment_id)
        if earned is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        reason = command.reason.strip()
        if not reason:
            raise DomainError("validation_error", "reason is required.")
        existing = [
            row
            for row in self._ledger.list_for_tenant(earned.tenant_id)
            if row.kind is LedgerKind.COMMISSION_REVERSAL
            and row.commission_id == earned.id
        ]
        if existing:
            return existing[0]
        now = self._clock.now()
        entry = LedgerEntryRecord(
            id=new_uuid7(),
            tenant_id=earned.tenant_id,
            customer_id=earned.customer_id,
            kind=LedgerKind.COMMISSION_REVERSAL,
            amount_minor=earned.amount_minor,
            currency=earned.currency,
            payment_id=earned.payment_id,
            invoice_id=earned.invoice_id,
            commission_id=earned.id,
            payout_id=None,
            eligible_base_minor=earned.eligible_base_minor,
            rate_bps_snapshot=earned.rate_bps_snapshot,
            earned_at=earned.earned_at,
            available_at=earned.available_at,
            reason=reason[:255],
            actor_id=command.actor_id,
            created_at=now,
        )
        self._ledger.append(entry)
        log_event(
            logger,
            "commission.reversed",
            outcome="success",
            tenant_id=str(earned.tenant_id),
            payment_id=str(command.payment_id),
            reason=reason[:64],
        )
        return entry
