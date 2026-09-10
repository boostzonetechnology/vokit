from __future__ import annotations

import logging
import uuid

from control_plane.tenancy.application.ports import Clock, TenantRecord, TenantRepository
from control_plane.tenancy.domain.lifecycle import (
    AgencyCapabilities,
    AgencyStatus,
    apply_agency_status_action,
)
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event
from tenant.lifecycle.domain import AgencyProfile
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.tenancy")


def _require_tenant(tenants: TenantRepository, tenant_id: uuid.UUID) -> TenantRecord:
    tenant = tenants.get(tenant_id)
    if tenant is None:
        raise DomainError("not_found", "Resource not found.", http_status=404)
    return tenant


def _sync_profile(
    lifecycle: TenantLifecycleService,
    tenant: TenantRecord,
    clock: Clock,
) -> None:
    lifecycle.put_agency(
        tenant.id,
        AgencyProfile(
            tenant_id=tenant.id,
            display_name=tenant.display_name,
            legal_name=tenant.legal_name,
            status=tenant.agency_status,
            currency=tenant.currency,
            capabilities=tenant.capabilities,
            updated_at=clock.now(),
        ),
    )


class ChangeAgencyStatus:
    def __init__(
        self,
        tenants: TenantRepository,
        lifecycle: TenantLifecycleService,
        clock: Clock,
    ) -> None:
        self._tenants = tenants
        self._lifecycle = lifecycle
        self._clock = clock

    def execute(self, tenant_id: uuid.UUID, action: str) -> TenantRecord:
        tenant = _require_tenant(self._tenants, tenant_id)
        nxt = apply_agency_status_action(tenant.agency_status, action)
        capabilities = tenant.capabilities
        if nxt is AgencyStatus.SUSPENDED:
            capabilities = AgencyCapabilities(
                create_customers=False,
                create_agents=capabilities.create_agents,
                purchase_numbers=capabilities.purchase_numbers,
                request_payouts=capabilities.request_payouts,
                existing_customer_services=capabilities.existing_customer_services,
            )
        updated = tenant.with_agency(agency_status=nxt, capabilities=capabilities)
        self._tenants.update(updated)
        _sync_profile(self._lifecycle, updated, self._clock)
        log_event(
            logger,
            "agency.status.changed",
            outcome="success",
            tenant_id=str(tenant_id),
            status=nxt.value,
        )
        return self._tenants.get(tenant_id) or updated


class ChangeAgencyCapabilities:
    def __init__(
        self,
        tenants: TenantRepository,
        lifecycle: TenantLifecycleService,
        clock: Clock,
    ) -> None:
        self._tenants = tenants
        self._lifecycle = lifecycle
        self._clock = clock

    def execute(
        self, tenant_id: uuid.UUID, capabilities: AgencyCapabilities
    ) -> TenantRecord:
        tenant = _require_tenant(self._tenants, tenant_id)
        if tenant.agency_status is AgencyStatus.CLOSED:
            raise DomainError(
                "agency_closed",
                "A closed agency cannot change capabilities.",
                http_status=409,
            )
        updated = tenant.with_agency(capabilities=capabilities)
        self._tenants.update(updated)
        _sync_profile(self._lifecycle, updated, self._clock)
        log_event(
            logger,
            "agency.capabilities.changed",
            outcome="success",
            tenant_id=str(tenant_id),
        )
        return self._tenants.get(tenant_id) or updated


class UpdateAgencyProfile:
    def __init__(
        self,
        tenants: TenantRepository,
        lifecycle: TenantLifecycleService,
        clock: Clock,
    ) -> None:
        self._tenants = tenants
        self._lifecycle = lifecycle
        self._clock = clock

    def execute(
        self,
        tenant_id: uuid.UUID,
        *,
        display_name: str | None,
        legal_name: str | None,
    ) -> TenantRecord:
        tenant = _require_tenant(self._tenants, tenant_id)
        name = tenant.display_name if display_name is None else display_name.strip()
        legal = tenant.legal_name if legal_name is None else legal_name.strip()
        if not name:
            raise DomainError("validation_error", "display_name is required.")
        updated = tenant.with_agency(display_name=name, legal_name=legal)
        self._tenants.update(updated)
        _sync_profile(self._lifecycle, updated, self._clock)
        log_event(
            logger,
            "agency.profile.changed",
            outcome="success",
            tenant_id=str(tenant_id),
        )
        return self._tenants.get(tenant_id) or updated


class SetCommissionRate:
    def __init__(self, tenants: TenantRepository, clock: Clock) -> None:
        self._tenants = tenants
        self._clock = clock

    def execute(self, tenant_id: uuid.UUID, rate_bps: int) -> TenantRecord:
        if rate_bps < 0 or rate_bps > 10000:
            raise DomainError("validation_error", "commission_rate_bps is invalid.")
        tenant = _require_tenant(self._tenants, tenant_id)
        updated = tenant.with_agency(
            commission_rate_bps=rate_bps,
            rate_effective_at=self._clock.now(),
        )
        self._tenants.update(updated)
        log_event(
            logger,
            "agency.commission.changed",
            outcome="success",
            tenant_id=str(tenant_id),
        )
        return self._tenants.get(tenant_id) or updated
