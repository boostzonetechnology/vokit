from __future__ import annotations

import logging
from dataclasses import dataclass

from control_plane.kyc.application.ports import (
    KycCaseRecord,
    KycCaseRepository,
    KycEventRepository,
    MappedProviderEvent,
)
from control_plane.kyc.domain.types import ProviderEventStatus
from control_plane.notifications.application.hooks import kyc_notify
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.kyc")


@dataclass(frozen=True, slots=True)
class WebhookResult:
    duplicate: bool
    status: str


class ApplyKycWebhook:
    def __init__(
        self,
        cases: KycCaseRepository,
        events: KycEventRepository,
    ) -> None:
        self._cases = cases
        self._events = events

    def execute(self, event: MappedProviderEvent) -> WebhookResult:
        if not event.event_id.strip():
            raise DomainError("validation_error", "event_id is required.")
        existing = self._events.get_by_event_id(event.event_id)
        if existing is not None:
            return WebhookResult(duplicate=True, status=existing.value)
        case = self._cases.get_by_session(event.session_id)
        if case is None:
            self._events.record(
                event_id=event.event_id,
                case_id=None,
                mapped_status=event.status,
                reason_code=event.reason_code,
                status=ProviderEventStatus.REJECTED,
            )
            raise DomainError(
                "kyc_case_not_found",
                "KYC session is not recognized.",
                http_status=404,
            )
        updated = KycCaseRecord(
            id=case.id,
            tenant_id=case.tenant_id,
            status=event.status,
            provider_slug=case.provider_slug,
            session_id=case.session_id,
            inquiry_id=event.inquiry_id or case.inquiry_id,
            last_event_id=event.event_id,
            reason_code=event.reason_code[:64],
            external_note=event.external_note[:255],
            internal_note=case.internal_note,
            frozen=case.frozen,
            expires_at=case.expires_at,
            created_at=case.created_at,
        )
        self._cases.update(updated)
        self._events.record(
            event_id=event.event_id,
            case_id=case.id,
            mapped_status=event.status,
            reason_code=event.reason_code,
            status=ProviderEventStatus.PROCESSED,
        )
        kyc_notify(tenant_id=case.tenant_id, status=event.status.value)
        log_event(
            logger,
            "kyc.status.changed",
            outcome="success",
            tenant_id=str(case.tenant_id),
            case_id=str(case.id),
            status=event.status.value,
            source="webhook",
        )
        return WebhookResult(duplicate=False, status=event.status.value)
