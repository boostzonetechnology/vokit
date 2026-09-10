from __future__ import annotations

from django.conf import settings

from control_plane.billing.infrastructure.container import (
    idempotency,
    invoice_index,
    tenant_billing,
)
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.risk.infrastructure.container import risk_gate, tenant_agents
from control_plane.telephony.application.assign import AssignNumber
from control_plane.telephony.application.destinations import ManageDestinations
from control_plane.telephony.application.reconcile import ReconcileNumbers
from control_plane.telephony.application.release import ReleaseNumber
from control_plane.telephony.application.reserve import ReserveNumber
from control_plane.telephony.application.search import SearchNumbers
from control_plane.telephony.application.session import VoiceControl, VoiceProviders
from control_plane.telephony.application.stock import PurchaseNumber, StockNumber
from control_plane.telephony.infrastructure.repositories import (
    DjangoCallIndexRepository,
    DjangoPhoneNumberRepository,
    DjangoReservationRepository,
    DjangoTrainingProposalRepository,
    DjangoTrainingSessionIndex,
    DjangoTransferIndexRepository,
)
from control_plane.tenancy.infrastructure.container import router, runtime, tenant_repo
from providers.telephony.edge import HttpSipEdge
from providers.telephony.memory import MemoryNumberProvider
from providers.telephony.memory_edge import MemorySipEdge
from shared_kernel.secrets import SecretRef
from tenant.calls.service import TenantCallService
from tenant.lifecycle.service import TenantLifecycleService
from tenant.media.service import TenantMediaService
from tenant.numbers.service import TenantNumberService

_provider: MemoryNumberProvider | None = None
_edge: MemorySipEdge | HttpSipEdge | None = None


def reset_number_provider() -> None:
    global _provider
    if _provider is not None:
        _provider.reset()
    _provider = None


def reset_sip_edge() -> None:
    global _edge
    if isinstance(_edge, MemorySipEdge):
        _edge.reset()
    _edge = None


def numbers() -> DjangoPhoneNumberRepository:
    return DjangoPhoneNumberRepository()


def reservations() -> DjangoReservationRepository:
    return DjangoReservationRepository()


def number_provider() -> MemoryNumberProvider:
    global _provider
    if _provider is None:
        _provider = MemoryNumberProvider()
    return _provider


def tenant_numbers() -> TenantNumberService:
    return TenantNumberService(router(), runtime())


def tenant_lifecycle() -> TenantLifecycleService:
    return TenantLifecycleService(router(), runtime())


def reservation_seconds() -> int:
    return int(getattr(settings, "NUMBER_RESERVATION_SECONDS", 600))


def stock_number() -> StockNumber:
    return StockNumber(numbers(), SystemClock())


def purchase_number() -> PurchaseNumber:
    return PurchaseNumber(numbers(), number_provider(), SystemClock())


def search_numbers() -> SearchNumbers:
    return SearchNumbers(numbers(), reservations(), number_provider(), SystemClock())


def reserve_number() -> ReserveNumber:
    return ReserveNumber(
        numbers(),
        reservations(),
        tenant_agents(),
        tenant_lifecycle(),
        SystemClock(),
    )


def assign_number() -> AssignNumber:
    return AssignNumber(
        numbers(),
        reservations(),
        tenant_repo(),
        tenant_agents(),
        tenant_lifecycle(),
        tenant_numbers(),
        tenant_billing(),
        invoice_index(),
        idempotency(),
        risk_gate(),
        SystemClock(),
    )


def release_number() -> ReleaseNumber:
    return ReleaseNumber(
        numbers(),
        reservations(),
        tenant_numbers(),
        number_provider(),
        SystemClock(),
    )


def reconcile_numbers() -> ReconcileNumbers:
    return ReconcileNumbers(numbers(), reservations(), number_provider(), SystemClock())


def tenant_calls() -> TenantCallService:
    return TenantCallService(router(), runtime())


def tenant_media() -> TenantMediaService:
    return TenantMediaService(router(), runtime())


def sip_edge():
    global _edge
    if _edge is None:
        url = str(getattr(settings, "SIP_EDGE_CONTROL_URL", "") or "").strip()
        if url:
            _edge = HttpSipEdge(url)
        else:
            _edge = MemorySipEdge()
    return _edge


def manage_destinations() -> ManageDestinations:
    from control_plane.customers.infrastructure.container import customer_index

    return ManageDestinations(
        customer_index(),
        tenant_media(),
        DjangoTransferIndexRepository(),
        SystemClock(),
    )


def voice_providers() -> VoiceProviders:
    def _spec(kind: str) -> dict[str, str]:
        code = str(getattr(settings, f"VOICE_{kind}_PROVIDER", "") or "").strip()
        ref = str(getattr(settings, f"VOICE_{kind}_API_KEY_REF", "") or "").strip()
        key = SecretRef(ref).resolve_optional() if ref else ""
        return {"provider_code": code, "api_key": key, "model": "", "language": "en"}

    return VoiceProviders(stt=_spec("STT"), tts=_spec("TTS"), llm=_spec("LLM"))


def _integration_gateway():
    from control_plane.integrations.infrastructure.container import integration_gateway

    return integration_gateway()


def _outbound_events():
    from control_plane.integrations.infrastructure.container import outbound_events

    return outbound_events()


def voice_control() -> VoiceControl:
    from control_plane.agents.infrastructure.container import global_instructions
    from control_plane.billing.infrastructure.container import plan_versions

    return VoiceControl(
        numbers(),
        tenant_agents(),
        tenant_lifecycle(),
        tenant_billing(),
        plan_versions(),
        tenant_calls(),
        DjangoCallIndexRepository(),
        DjangoTrainingProposalRepository(),
        DjangoTrainingSessionIndex(),
        global_instructions(),
        risk_gate(),
        SystemClock(),
        voice_providers(),
        tenant_media(),
        DjangoTransferIndexRepository(),
        sip_edge(),
        idempotency(),
        tools=_integration_gateway(),
        events=_outbound_events(),
    )
