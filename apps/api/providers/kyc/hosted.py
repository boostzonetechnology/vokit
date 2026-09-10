from __future__ import annotations

from control_plane.kyc.application.ports import (
    KycCaseRecord,
    KycSettingsRecord,
    ProviderSession,
)
from shared_kernel.ids import new_uuid7
from shared_kernel.secrets import SecretRef


class HostedKycAdapter:
    """Vendor-neutral hosted session. Domain never imports a KYC SDK."""

    slug = "external"

    def start_or_resume(
        self, settings: KycSettingsRecord, case: KycCaseRecord | None
    ) -> ProviderSession:
        SecretRef(settings.api_key_ref).resolve()
        if case is not None and case.session_id and case.inquiry_id:
            return ProviderSession(
                session_id=case.session_id,
                inquiry_id=case.inquiry_id,
                hosted_url=_hosted_url(settings.hosted_base_url, case.session_id),
            )
        session_id = f"kycsess_{new_uuid7()}"
        inquiry_id = f"kycinq_{new_uuid7()}"
        return ProviderSession(
            session_id=session_id,
            inquiry_id=inquiry_id,
            hosted_url=_hosted_url(settings.hosted_base_url, session_id),
        )


def _hosted_url(base: str, session_id: str) -> str:
    return f"{base.rstrip('/')}/session/{session_id}"
