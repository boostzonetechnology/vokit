from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.kyc.application.ports import KycCaseRepository
from control_plane.kyc.domain.policies import assert_payout_eligible
from control_plane.tenancy.application.ports import TenantRepository
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.kyc")


@dataclass(frozen=True, slots=True)
class PayoutGateResult:
    accepted: bool
    kyc_status: str


class RequestPayout:
    """Phase 5 gate only. Ledger settlement is Phase 7."""

    def __init__(
        self,
        cases: KycCaseRepository,
        tenants: TenantRepository,
    ) -> None:
        self._cases = cases
        self._tenants = tenants

    def execute(self, tenant_id: uuid.UUID) -> PayoutGateResult:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        case = self._cases.get_for_tenant(tenant_id)
        status = case.status if case is not None else None
        frozen = bool(case.frozen) if case is not None else False
        assert_payout_eligible(
            kyc_status=status,
            frozen=frozen,
            agency_status=tenant.agency_status,
            capabilities=tenant.capabilities,
        )
        log_event(
            logger,
            "payout.requested",
            outcome="accepted",
            tenant_id=str(tenant_id),
            kyc_status=status.value if status else "unknown",
        )
        return PayoutGateResult(
            accepted=True,
            kyc_status=status.value if status else "unknown",
        )
