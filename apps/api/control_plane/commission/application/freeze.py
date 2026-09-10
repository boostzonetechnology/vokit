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
from shared_kernel.money import V1_CURRENCY

logger = logging.getLogger("vokit.commission")


@dataclass(frozen=True, slots=True)
class FreezeWalletCommand:
    tenant_id: uuid.UUID
    frozen: bool
    reason: str
    actor_id: uuid.UUID


class FreezeWallet:
    def __init__(self, ledger: LedgerRepository, clock: Clock) -> None:
        self._ledger = ledger
        self._clock = clock

    def execute(self, command: FreezeWalletCommand) -> LedgerEntryRecord:
        reason = command.reason.strip()
        if not reason:
            raise DomainError("validation_error", "reason is required.")
        now = self._clock.now()
        entry = LedgerEntryRecord(
            id=new_uuid7(),
            tenant_id=command.tenant_id,
            customer_id=None,
            kind=LedgerKind.WALLET_FROZEN if command.frozen else LedgerKind.WALLET_UNFROZEN,
            amount_minor=0,
            currency=V1_CURRENCY,
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
                action="wallet.frozen",
                entity_type="wallet_ledger",
                entity_id=str(entry.id),
                actor_id=command.actor_id,
                tenant_id=command.tenant_id,
                reason=reason,
                after_summary="frozen" if command.frozen else "unfrozen",
            )
        )
        log_event(
            logger,
            "wallet.freeze.changed",
            outcome="success",
            tenant_id=str(command.tenant_id),
            frozen=command.frozen,
        )
        return entry
