from __future__ import annotations

from django.conf import settings

from control_plane.customers.infrastructure.container import customer_index
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.integrations.application.service import IntegrationControl
from control_plane.integrations.infrastructure.repositories import (
    DjangoConnectionIndexRepository,
    DjangoEndpointIndexRepository,
)
from control_plane.tenancy.infrastructure.container import router, runtime
from providers.integrations.adapters import MemoryIntegrationAdapter, MemoryWebhookTransport
from providers.integrations.vault import MemorySecretVault
from tenant.agents.service import TenantAgentService
from tenant.integrations.service import TenantIntegrationService

_vault: MemorySecretVault | None = None
_adapter: MemoryIntegrationAdapter | None = None
_transport: MemoryWebhookTransport | None = None


def reset_integrations() -> None:
    global _vault, _adapter, _transport
    if _vault is not None:
        _vault.reset()
    if _adapter is not None:
        _adapter.reset()
    if _transport is not None:
        _transport.reset()
    _vault = None
    _adapter = None
    _transport = None


def secret_vault() -> MemorySecretVault:
    global _vault
    if _vault is None:
        _vault = MemorySecretVault()
    return _vault


def integration_adapter() -> MemoryIntegrationAdapter:
    global _adapter
    if _adapter is None:
        _adapter = MemoryIntegrationAdapter()
    return _adapter


def webhook_transport() -> MemoryWebhookTransport:
    global _transport
    if _transport is None:
        _transport = MemoryWebhookTransport()
    return _transport


def tenant_integrations() -> TenantIntegrationService:
    return TenantIntegrationService(router(), runtime())


def integration_control() -> IntegrationControl:
    return IntegrationControl(
        customer_index(),
        tenant_integrations(),
        TenantAgentService(router(), runtime()),
        DjangoConnectionIndexRepository(),
        DjangoEndpointIndexRepository(),
        secret_vault(),
        integration_adapter(),
        webhook_transport(),
        SystemClock(),
        allow_http=bool(getattr(settings, "INTEGRATION_ALLOW_HTTP", False)),
    )


def integration_gateway() -> IntegrationControl:
    return integration_control()


def outbound_events() -> IntegrationControl:
    return integration_control()
