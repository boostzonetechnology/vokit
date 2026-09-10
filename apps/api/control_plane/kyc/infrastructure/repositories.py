from __future__ import annotations

import uuid

from django.conf import settings

from control_plane.kyc.application.ports import KycCaseRecord, KycSettingsRecord
from control_plane.kyc.domain.types import KycStatus, ProviderEventStatus
from control_plane.kyc.models import KycCase, KycProviderEvent, KycSettings
from shared_kernel.errors import DomainError
from shared_kernel.secrets import SecretRef


def _case(row: KycCase) -> KycCaseRecord:
    return KycCaseRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        status=KycStatus(row.status),
        provider_slug=row.provider_slug,
        session_id=row.session_id,
        inquiry_id=row.inquiry_id,
        last_event_id=row.last_event_id,
        reason_code=row.reason_code,
        external_note=row.external_note,
        internal_note=row.internal_note,
        frozen=row.frozen,
        expires_at=row.expires_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class DjangoKycCaseRepository:
    def get(self, case_id: uuid.UUID) -> KycCaseRecord | None:
        row = KycCase.objects.filter(id=case_id).first()
        return _case(row) if row else None

    def get_for_tenant(self, tenant_id: uuid.UUID) -> KycCaseRecord | None:
        row = KycCase.objects.filter(tenant_id=tenant_id).first()
        return _case(row) if row else None

    def get_by_session(self, session_id: str) -> KycCaseRecord | None:
        if not session_id:
            return None
        row = KycCase.objects.filter(session_id=session_id).first()
        return _case(row) if row else None

    def list(self, *, status: KycStatus | None = None) -> list[KycCaseRecord]:
        rows = KycCase.objects.order_by("created_at")
        if status is not None:
            rows = rows.filter(status=status.value)
        return [_case(row) for row in rows]

    def create(self, record: KycCaseRecord) -> None:
        KycCase.objects.create(
            id=record.id,
            tenant_id=record.tenant_id,
            status=record.status.value,
            provider_slug=record.provider_slug,
            session_id=record.session_id,
            inquiry_id=record.inquiry_id,
            last_event_id=record.last_event_id,
            reason_code=record.reason_code,
            external_note=record.external_note,
            internal_note=record.internal_note,
            frozen=record.frozen,
            expires_at=record.expires_at,
        )

    def update(self, record: KycCaseRecord) -> None:
        KycCase.objects.filter(id=record.id).update(
            status=record.status.value,
            provider_slug=record.provider_slug,
            session_id=record.session_id,
            inquiry_id=record.inquiry_id,
            last_event_id=record.last_event_id,
            reason_code=record.reason_code,
            external_note=record.external_note,
            internal_note=record.internal_note,
            frozen=record.frozen,
            expires_at=record.expires_at,
        )


class DjangoKycSettingsRepository:
    def get(self) -> KycSettingsRecord:
        row = KycSettings.objects.order_by("updated_at").first()
        if row is None:
            return KycSettingsRecord(
                provider_slug=getattr(settings, "KYC_PROVIDER", "external"),
                api_key_ref=getattr(settings, "KYC_API_KEY_REF", "KYC_API_KEY"),
                webhook_secret_ref=getattr(
                    settings, "KYC_WEBHOOK_SECRET_REF", "KYC_WEBHOOK_SECRET"
                ),
                hosted_base_url=getattr(
                    settings, "KYC_HOSTED_BASE_URL", "https://kyc.example.test"
                ),
            )
        return KycSettingsRecord(
            provider_slug=row.provider_slug,
            api_key_ref=row.api_key_ref,
            webhook_secret_ref=row.webhook_secret_ref,
            hosted_base_url=row.hosted_base_url,
        )

    def save(self, record: KycSettingsRecord) -> None:
        SecretRef(record.api_key_ref)
        SecretRef(record.webhook_secret_ref)
        base = record.hosted_base_url.strip()
        allowed_http = bool(getattr(settings, "KYC_ALLOW_HTTP_HOSTED", False))
        if base.startswith("https://") or (allowed_http and base.startswith("http://")):
            pass
        else:
            raise DomainError("validation_error", "hosted_base_url is invalid.")
        row = KycSettings.objects.order_by("updated_at").first()
        if row is None:
            KycSettings.objects.create(
                provider_slug=record.provider_slug,
                api_key_ref=record.api_key_ref,
                webhook_secret_ref=record.webhook_secret_ref,
                hosted_base_url=record.hosted_base_url,
            )
            return
        row.provider_slug = record.provider_slug
        row.api_key_ref = record.api_key_ref
        row.webhook_secret_ref = record.webhook_secret_ref
        row.hosted_base_url = record.hosted_base_url
        row.save()


class DjangoKycEventRepository:
    def get_by_event_id(self, event_id: str) -> ProviderEventStatus | None:
        row = KycProviderEvent.objects.filter(event_id=event_id).first()
        if row is None:
            return None
        return ProviderEventStatus(row.status)

    def record(
        self,
        *,
        event_id: str,
        case_id: uuid.UUID | None,
        mapped_status: KycStatus | None,
        reason_code: str,
        status: ProviderEventStatus,
    ) -> None:
        KycProviderEvent.objects.update_or_create(
            event_id=event_id,
            defaults={
                "case_id": case_id,
                "mapped_status": mapped_status.value if mapped_status else "",
                "reason_code": reason_code[:64],
                "status": status.value,
            },
        )
