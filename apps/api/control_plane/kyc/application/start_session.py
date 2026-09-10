from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.kyc.application.ports import (
    KycCaseRecord,
    KycCaseRepository,
    KycProvider,
    KycSettingsRepository,
    ProviderSession,
)
from control_plane.kyc.domain.types import KycStatus
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.kyc")


@dataclass(frozen=True, slots=True)
class StartedKycSession:
    case: KycCaseRecord
    session: ProviderSession


class StartKycSession:
    def __init__(
        self,
        cases: KycCaseRepository,
        settings: KycSettingsRepository,
        provider: KycProvider,
    ) -> None:
        self._cases = cases
        self._settings = settings
        self._provider = provider

    def execute(self, tenant_id: uuid.UUID) -> StartedKycSession:
        settings = self._settings.get()
        existing = self._cases.get_for_tenant(tenant_id)
        session = self._provider.start_or_resume(settings, existing)
        if existing is None:
            record = KycCaseRecord(
                id=new_uuid7(),
                tenant_id=tenant_id,
                status=KycStatus.INCOMPLETE,
                provider_slug=self._provider.slug,
                session_id=session.session_id,
                inquiry_id=session.inquiry_id,
                last_event_id="",
                reason_code="",
                external_note="",
                internal_note="",
                frozen=False,
            )
            self._cases.create(record)
            case = self._cases.get_for_tenant(tenant_id) or record
        else:
            record = KycCaseRecord(
                id=existing.id,
                tenant_id=existing.tenant_id,
                status=existing.status
                if existing.status is not KycStatus.NOT_STARTED
                else KycStatus.INCOMPLETE,
                provider_slug=self._provider.slug,
                session_id=session.session_id,
                inquiry_id=session.inquiry_id,
                last_event_id=existing.last_event_id,
                reason_code=existing.reason_code,
                external_note=existing.external_note,
                internal_note=existing.internal_note,
                frozen=existing.frozen,
                expires_at=existing.expires_at,
                created_at=existing.created_at,
            )
            self._cases.update(record)
            case = self._cases.get_for_tenant(tenant_id) or record
        log_event(
            logger,
            "kyc.session.started",
            outcome="success",
            tenant_id=str(tenant_id),
            case_id=str(case.id),
        )
        return StartedKycSession(case=case, session=session)
