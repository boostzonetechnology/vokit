from __future__ import annotations

import logging
import uuid
from datetime import datetime

from control_plane.audit.application.record import RecordAudit, RecordAuditCommand
from control_plane.notifications.application.hooks import kyc_notify
from control_plane.tenancy.application.ports import Clock, TenantRecord, TenantRepository
from control_plane.tenancy.domain.commission import (
    assert_commission_reason,
    effective_commission_rate_bps,
)
from control_plane.tenancy.domain.lifecycle import (
    AgencyCapabilities,
    AgencyStatus,
    apply_agency_status_action,
    assert_agency_action_confirmed,
    assert_agency_status_reason,
    default_capabilities_for_status,
    merge_capability_gates,
)
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event
from tenant.lifecycle.domain import AgencyProfile
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.tenancy")


def _caps_summary(caps: AgencyCapabilities) -> str:
    return (
        f"customers={int(caps.create_customers)}"
        f"|agents={int(caps.create_agents)}"
        f"|numbers={int(caps.purchase_numbers)}"
        f"|payouts={int(caps.request_payouts)}"
        f"|existing={int(caps.existing_customer_services)}"
    )


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
        audit: RecordAudit,
    ) -> None:
        self._tenants = tenants
        self._lifecycle = lifecycle
        self._clock = clock
        self._audit = audit

    def execute(
        self,
        tenant_id: uuid.UUID,
        action: str,
        *,
        confirm: bool = False,
        reason: str = "",
        actor_id: uuid.UUID | None = None,
        actor_role: str = "",
    ) -> TenantRecord:
        assert_agency_action_confirmed(confirm)
        assert_agency_status_reason(action, reason)
        tenant = _require_tenant(self._tenants, tenant_id)
        nxt = apply_agency_status_action(tenant.agency_status, action)
        capabilities = merge_capability_gates(
            tenant.capabilities, default_capabilities_for_status(nxt)
        )
        updated = tenant.with_agency(agency_status=nxt, capabilities=capabilities)
        self._tenants.update(updated)
        _sync_profile(self._lifecycle, updated, self._clock)
        self._audit.execute(
            RecordAuditCommand(
                action="agency.status.changed",
                entity_type="agency",
                entity_id=str(tenant_id),
                actor_id=actor_id,
                actor_role=actor_role,
                tenant_id=tenant_id,
                reason=reason,
                before_summary=tenant.agency_status.value,
                after_summary=nxt.value,
            )
        )
        if nxt is AgencyStatus.SUSPENDED:
            kyc_notify(tenant_id=tenant_id, status="suspended")
        elif nxt is AgencyStatus.RESTRICTED:
            kyc_notify(tenant_id=tenant_id, status="restricted")
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
        audit: RecordAudit,
    ) -> None:
        self._tenants = tenants
        self._lifecycle = lifecycle
        self._clock = clock
        self._audit = audit

    def execute(
        self,
        tenant_id: uuid.UUID,
        capabilities: AgencyCapabilities,
        *,
        confirm: bool = False,
        reason: str = "",
        actor_id: uuid.UUID | None = None,
        actor_role: str = "",
    ) -> TenantRecord:
        assert_agency_action_confirmed(confirm)
        if not reason.strip():
            raise DomainError("validation_error", "reason is required.")
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
        self._audit.execute(
            RecordAuditCommand(
                action="agency.capabilities.changed",
                entity_type="agency",
                entity_id=str(tenant_id),
                actor_id=actor_id,
                actor_role=actor_role,
                tenant_id=tenant_id,
                reason=reason,
                before_summary=_caps_summary(tenant.capabilities),
                after_summary=_caps_summary(capabilities),
            )
        )
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
        audit: RecordAudit,
    ) -> None:
        self._tenants = tenants
        self._lifecycle = lifecycle
        self._clock = clock
        self._audit = audit

    def execute(
        self,
        tenant_id: uuid.UUID,
        *,
        display_name: str | None,
        legal_name: str | None,
        actor_id: uuid.UUID | None = None,
        actor_role: str = "",
    ) -> TenantRecord:
        tenant = _require_tenant(self._tenants, tenant_id)
        name = tenant.display_name if display_name is None else display_name.strip()
        legal = tenant.legal_name if legal_name is None else legal_name.strip()
        if not name:
            raise DomainError("validation_error", "display_name is required.")
        updated = tenant.with_agency(display_name=name, legal_name=legal)
        self._tenants.update(updated)
        _sync_profile(self._lifecycle, updated, self._clock)
        self._audit.execute(
            RecordAuditCommand(
                action="agency.profile.changed",
                entity_type="agency",
                entity_id=str(tenant_id),
                actor_id=actor_id,
                actor_role=actor_role,
                tenant_id=tenant_id,
                before_summary=f"{tenant.display_name}|{tenant.legal_name}",
                after_summary=f"{name}|{legal}",
            )
        )
        log_event(
            logger,
            "agency.profile.changed",
            outcome="success",
            tenant_id=str(tenant_id),
        )
        return self._tenants.get(tenant_id) or updated


class SetCommissionRate:
    def __init__(
        self, tenants: TenantRepository, clock: Clock, audit: RecordAudit
    ) -> None:
        self._tenants = tenants
        self._clock = clock
        self._audit = audit

    def execute(
        self,
        tenant_id: uuid.UUID,
        rate_bps: int,
        *,
        rate_effective_at: datetime | None = None,
        reason: str = "",
        actor_id: uuid.UUID | None = None,
        actor_role: str = "",
    ) -> TenantRecord:
        if rate_bps < 0 or rate_bps > 10000:
            raise DomainError("validation_error", "commission_rate_bps is invalid.")
        assert_commission_reason(reason)
        tenant = _require_tenant(self._tenants, tenant_id)
        now = self._clock.now()
        if rate_effective_at is not None and rate_effective_at < now:
            raise DomainError(
                "validation_error",
                "rate_effective_at cannot be in the past.",
            )
        effective_at = now if rate_effective_at is None else rate_effective_at
        live = effective_commission_rate_bps(
            rate_bps=tenant.commission_rate_bps,
            previous_rate_bps=tenant.previous_commission_rate_bps,
            rate_effective_at=tenant.rate_effective_at,
            at=now,
        )
        updated = tenant.with_agency(
            commission_rate_bps=rate_bps,
            previous_commission_rate_bps=live,
            rate_effective_at=effective_at,
        )
        self._tenants.update(updated)
        self._audit.execute(
            RecordAuditCommand(
                action="agency.commission.changed",
                entity_type="agency",
                entity_id=str(tenant_id),
                actor_id=actor_id,
                actor_role=actor_role,
                tenant_id=tenant_id,
                reason=reason,
                before_summary=str(tenant.commission_rate_bps),
                after_summary=str(rate_bps),
            )
        )
        log_event(
            logger,
            "agency.commission.changed",
            outcome="success",
            tenant_id=str(tenant_id),
        )
        return self._tenants.get(tenant_id) or updated
