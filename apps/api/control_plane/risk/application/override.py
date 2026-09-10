from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.audit.application.record import RecordAuditCommand
from control_plane.audit.infrastructure.container import record_audit
from control_plane.risk.application.ports import RiskCaseRecord, RiskCaseRepository
from control_plane.risk.domain.policies import assert_agency_cannot_override
from control_plane.risk.domain.types import RiskStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.risk")


@dataclass(frozen=True, slots=True)
class OverrideRiskCommand:
    case_id: uuid.UUID
    status: RiskStatus
    note: str
    privileged: bool


class OverrideRisk:
    def __init__(self, cases: RiskCaseRepository, clock: Clock) -> None:
        self._cases = cases
        self._clock = clock

    def execute(self, command: OverrideRiskCommand) -> RiskCaseRecord:
        if not command.privileged:
            assert_agency_cannot_override()
        case = self._cases.get(command.case_id)
        if case is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        updated = RiskCaseRecord(
            id=case.id,
            tenant_id=case.tenant_id,
            customer_id=case.customer_id,
            status=command.status,
            last_invoice_id=case.last_invoice_id,
            last_payment_id=case.last_payment_id,
            last_event_id=case.last_event_id,
            note=command.note.strip()[:255] or case.note,
            permanently_banned=case.permanently_banned
            or command.status is RiskStatus.PERMANENTLY_BANNED,
            created_at=case.created_at,
            updated_at=self._clock.now(),
        )
        self._cases.upsert(updated)
        record_audit().execute(
            RecordAuditCommand(
                action="risk.override",
                entity_type="risk_case",
                entity_id=str(case.id),
                tenant_id=case.tenant_id,
                customer_id=case.customer_id,
                reason=command.note,
                before_summary=case.status.value,
                after_summary=command.status.value,
            )
        )
        log_event(
            logger,
            "risk.override",
            outcome="success",
            tenant_id=str(case.tenant_id),
            customer_id=str(case.customer_id),
            case_id=str(case.id),
            status=command.status.value,
        )
        return self._cases.get(case.id) or updated
