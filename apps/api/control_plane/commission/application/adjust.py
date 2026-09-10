from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.audit.application.record import RecordAuditCommand
from control_plane.audit.infrastructure.container import record_audit
from control_plane.commission.application.ports import LedgerEntryRecord, LedgerRepository
from control_plane.commission.domain.types import LedgerKind
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from shared_kernel.money import Money

logger = logging.getLogger("vokit.commission")


@dataclass(frozen=True, slots=True)
class AdjustWalletCommand:
    tenant_id: uuid.UUID
    amount_minor: int
    direction: str
    reason: str
    actor_id: uuid.UUID


class AdjustWallet:
    def __init__(self, ledger: LedgerRepository, clock: Clock) -> None:
        self._ledger = ledger
        self._clock = clock

    def execute(self, command: AdjustWalletCommand) -> LedgerEntryRecord:
        reason = command.reason.strip()
        if not reason:
            raise DomainError("validation_error", "reason is required.")
        direction = command.direction.strip().lower()
        if direction == "credit":
            kind = LedgerKind.MANUAL_CREDIT
        elif direction == "debit":
            kind = LedgerKind.MANUAL_DEBIT
        else:
            raise DomainError("validation_error", "direction must be credit or debit.")
        amount = Money(command.amount_minor)
        if amount.minor_units < 1:
            raise DomainError("validation_error", "amount_minor must be a positive integer.")
        now = self._clock.now()
        entry = LedgerEntryRecord(
            id=new_uuid7(),
            tenant_id=command.tenant_id,
            customer_id=None,
            kind=kind,
            amount_minor=amount.minor_units,
            currency=amount.currency,
            payment_id=None,
            invoice_id=None,
            commission_id=None,
            payout_id=None,
            eligible_base_minor=None,
            rate_bps_snapshot=None,
            earned_at=now,
            available_at=now,
            reason=reason[:255],
            actor_id=command.actor_id,
            created_at=now,
        )
        self._ledger.append(entry)
        record_audit().execute(
            RecordAuditCommand(
                action="wallet.adjusted",
                entity_type="wallet_ledger",
                entity_id=str(entry.id),
                actor_id=command.actor_id,
                tenant_id=command.tenant_id,
                reason=reason,
                after_summary=direction,
                payload={"direction": direction, "amount_minor": amount.minor_units},
            )
        )
        log_event(
            logger,
            "wallet.adjusted",
            outcome="success",
            tenant_id=str(command.tenant_id),
            direction=direction,
        )
        return entry
