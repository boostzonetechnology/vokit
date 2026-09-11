from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.tenancy.domain.lifecycle import AgencyCapabilities, AgencyStatus
from control_plane.tenancy.domain.types import (
    DatabaseStatus,
    MigrationJobStatus,
    ProvisioningStep,
    TenantStatus,
)


@dataclass(frozen=True, slots=True)
class TenantRecord:
    id: uuid.UUID
    display_name: str
    status: TenantStatus
    created_at: datetime | None = None
    agency_status: AgencyStatus = AgencyStatus.PENDING
    legal_name: str = ""
    currency: str = "USD"
    commission_rate_bps: int = 0
    rate_effective_at: datetime | None = None
    capabilities: AgencyCapabilities = AgencyCapabilities()

    def with_agency(
        self,
        *,
        display_name: str | None = None,
        agency_status: AgencyStatus | None = None,
        legal_name: str | None = None,
        currency: str | None = None,
        commission_rate_bps: int | None = None,
        rate_effective_at: datetime | None = None,
        capabilities: AgencyCapabilities | None = None,
    ) -> TenantRecord:
        return TenantRecord(
            id=self.id,
            display_name=self.display_name if display_name is None else display_name,
            status=self.status,
            created_at=self.created_at,
            agency_status=self.agency_status
            if agency_status is None
            else agency_status,
            legal_name=self.legal_name if legal_name is None else legal_name,
            currency=self.currency if currency is None else currency,
            commission_rate_bps=(
                self.commission_rate_bps
                if commission_rate_bps is None
                else commission_rate_bps
            ),
            rate_effective_at=(
                self.rate_effective_at
                if rate_effective_at is None
                else rate_effective_at
            ),
            capabilities=self.capabilities if capabilities is None else capabilities,
        )


@dataclass(frozen=True, slots=True)
class TenantDatabaseRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    host: str
    port: int
    name: str
    secret_ref: str
    tls_required: bool
    status: DatabaseStatus
    schema_version: str
    last_health_at: datetime | None = None
    db_username: str = ""


@dataclass(frozen=True, slots=True)
class ProvisioningJobRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    step: ProvisioningStep
    attempts: int
    last_error: str


@dataclass(frozen=True, slots=True)
class MigrationJobRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    source_version: str
    target_version: str
    status: MigrationJobStatus
    canary: bool
    last_error: str


class TenantRepository(Protocol):
    def get(self, tenant_id: uuid.UUID) -> TenantRecord | None: ...
    def list(self) -> list[TenantRecord]: ...
    def create(self, tenant: TenantRecord) -> None: ...
    def update_status(self, tenant_id: uuid.UUID, status: TenantStatus) -> None: ...
    def update(self, tenant: TenantRecord) -> None: ...


class TenantDatabaseRepository(Protocol):
    def get_for_tenant(self, tenant_id: uuid.UUID) -> TenantDatabaseRecord | None: ...

    def get_by_username(self, db_username: str) -> TenantDatabaseRecord | None: ...

    def create(self, record: TenantDatabaseRecord) -> None: ...

    def update(self, record: TenantDatabaseRecord) -> None: ...


class ProvisioningJobRepository(Protocol):
    def get(self, job_id: uuid.UUID) -> ProvisioningJobRecord | None: ...
    def get_open_for_tenant(
        self, tenant_id: uuid.UUID
    ) -> ProvisioningJobRecord | None: ...
    def create(self, job: ProvisioningJobRecord) -> None: ...
    def update(self, job: ProvisioningJobRecord) -> None: ...


class MigrationJobRepository(Protocol):
    def get(self, job_id: uuid.UUID) -> MigrationJobRecord | None: ...
    def get_active_for_tenant(
        self, tenant_id: uuid.UUID
    ) -> MigrationJobRecord | None: ...
    def create(self, job: MigrationJobRecord) -> None: ...
    def update(self, job: MigrationJobRecord) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
