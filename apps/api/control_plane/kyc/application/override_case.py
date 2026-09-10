from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.audit.application.record import RecordAuditCommand
from control_plane.audit.infrastructure.container import record_audit
from control_plane.kyc.application.ports import KycCaseRecord, KycCaseRepository
from control_plane.kyc.domain.types import KycStatus
from control_plane.notifications.application.hooks import kyc_notify
from control_plane.tenancy.application.change_agency import ChangeAgencyCapabilities
from control_plane.tenancy.application.ports import TenantRepository
from control_plane.tenancy.domain.lifecycle import AgencyCapabilities
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.kyc")


@dataclass(frozen=True, slots=True)
class OverrideKycCommand:
    case_id: uuid.UUID
    action: str
    status: KycStatus | None = None
    internal_note: str = ""


class OverrideKycCase:
    def __init__(
        self,
        cases: KycCaseRepository,
        tenants: TenantRepository,
        capabilities: ChangeAgencyCapabilities,
    ) -> None:
        self._cases = cases
        self._tenants = tenants
        self._capabilities = capabilities

    def execute(self, command: OverrideKycCommand) -> KycCaseRecord:
        case = self._cases.get(command.case_id)
        if case is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        action = command.action.strip().lower()
        frozen = case.frozen
        status = case.status
        if action == "freeze":
            frozen = True
            self._freeze_payouts(case.tenant_id)
        elif action == "unfreeze":
            frozen = False
        elif action == "set_status":
            if command.status is None:
                raise DomainError("validation_error", "status is required.")
            status = command.status
        else:
            raise DomainError("validation_error", "Unknown KYC override action.")
        updated = KycCaseRecord(
            id=case.id,
            tenant_id=case.tenant_id,
            status=status,
            provider_slug=case.provider_slug,
            session_id=case.session_id,
            inquiry_id=case.inquiry_id,
            last_event_id=case.last_event_id,
            reason_code=case.reason_code,
            external_note=case.external_note,
            internal_note=command.internal_note[:255] or case.internal_note,
            frozen=frozen,
            expires_at=case.expires_at,
            created_at=case.created_at,
        )
        self._cases.update(updated)
        reason = command.internal_note.strip()
        record_audit().execute(
            RecordAuditCommand(
                action="kyc.override",
                entity_type="kyc_case",
                entity_id=str(case.id),
                tenant_id=case.tenant_id,
                reason=reason,
                before_summary=case.status.value,
                after_summary=status.value,
                payload={"action": action, "frozen": frozen},
            )
        )
        kyc_notify(tenant_id=case.tenant_id, status=status.value)
        log_event(
            logger,
            "kyc.override",
            outcome="success",
            tenant_id=str(case.tenant_id),
            case_id=str(case.id),
            action=action,
            status=status.value,
        )
        return self._cases.get(case.id) or updated

    def _freeze_payouts(self, tenant_id: uuid.UUID) -> None:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            return
        caps = tenant.capabilities
        self._capabilities.execute(
            tenant_id,
            AgencyCapabilities(
                create_customers=caps.create_customers,
                create_agents=caps.create_agents,
                purchase_numbers=caps.purchase_numbers,
                request_payouts=False,
                existing_customer_services=caps.existing_customer_services,
            ),
        )
