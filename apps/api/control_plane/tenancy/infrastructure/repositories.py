from __future__ import annotations

import uuid

from control_plane.tenancy.application.ports import (
    MigrationJobRecord,
    ProvisioningJobRecord,
    TenantDatabaseRecord,
    TenantRecord,
)
from control_plane.tenancy.domain.lifecycle import AgencyCapabilities, AgencyStatus
from control_plane.tenancy.domain.types import (
    DatabaseStatus,
    MigrationJobStatus,
    ProvisioningStep,
    TenantStatus,
)
from control_plane.tenancy.models import (
    Tenant,
    TenantDatabase,
    TenantMigrationJob,
    TenantProvisioningJob,
)


def _capabilities(row: Tenant) -> AgencyCapabilities:
    return AgencyCapabilities(
        create_customers=row.can_create_customers,
        create_agents=row.can_create_agents,
        purchase_numbers=row.can_purchase_numbers,
        request_payouts=row.can_request_payouts,
        existing_customer_services=row.existing_customer_services,
    )


def _tenant(row: Tenant) -> TenantRecord:
    return TenantRecord(
        id=row.id,
        display_name=row.display_name,
        status=TenantStatus(row.status),
        created_at=row.created_at,
        agency_status=AgencyStatus(row.agency_status),
        legal_name=row.legal_name,
        currency=row.currency,
        commission_rate_bps=row.commission_rate_bps,
        rate_effective_at=row.rate_effective_at,
        capabilities=_capabilities(row),
    )


def _database(row: TenantDatabase) -> TenantDatabaseRecord:
    return TenantDatabaseRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        host=row.host,
        port=row.port,
        name=row.name,
        secret_ref=row.secret_ref,
        tls_required=row.tls_required,
        status=DatabaseStatus(row.status),
        schema_version=row.schema_version,
        last_health_at=row.last_health_at,
        db_username=row.db_username,
    )


class DjangoTenantRepository:
    def get(self, tenant_id: uuid.UUID) -> TenantRecord | None:
        row = Tenant.objects.filter(id=tenant_id).first()
        return _tenant(row) if row else None

    def list(self) -> list[TenantRecord]:
        return [_tenant(row) for row in Tenant.objects.order_by("created_at")]

    def create(self, tenant: TenantRecord) -> None:
        Tenant.objects.create(
            id=tenant.id,
            display_name=tenant.display_name,
            status=tenant.status.value,
        )

    def update_status(self, tenant_id: uuid.UUID, status: TenantStatus) -> None:
        Tenant.objects.filter(id=tenant_id).update(status=status.value)

    def update(self, tenant: TenantRecord) -> None:
        Tenant.objects.filter(id=tenant.id).update(
            display_name=tenant.display_name,
            status=tenant.status.value,
            agency_status=tenant.agency_status.value,
            legal_name=tenant.legal_name,
            currency=tenant.currency,
            commission_rate_bps=tenant.commission_rate_bps,
            rate_effective_at=tenant.rate_effective_at,
            can_create_customers=tenant.capabilities.create_customers,
            can_create_agents=tenant.capabilities.create_agents,
            can_purchase_numbers=tenant.capabilities.purchase_numbers,
            can_request_payouts=tenant.capabilities.request_payouts,
            existing_customer_services=tenant.capabilities.existing_customer_services,
        )


class DjangoTenantDatabaseRepository:
    def get_for_tenant(self, tenant_id: uuid.UUID) -> TenantDatabaseRecord | None:
        row = TenantDatabase.objects.filter(tenant_id=tenant_id).first()
        return _database(row) if row else None

    def get_by_username(self, db_username: str) -> TenantDatabaseRecord | None:
        cleaned = (db_username or "").strip()
        if not cleaned:
            return None
        row = TenantDatabase.objects.filter(db_username=cleaned).first()
        return _database(row) if row else None

    def create(self, record: TenantDatabaseRecord) -> None:
        TenantDatabase.objects.create(
            id=record.id,
            tenant_id=record.tenant_id,
            host=record.host,
            port=record.port,
            name=record.name,
            db_username=record.db_username,
            secret_ref=record.secret_ref,
            tls_required=record.tls_required,
            status=record.status.value,
            schema_version=record.schema_version,
            last_health_at=record.last_health_at,
        )

    def update(self, record: TenantDatabaseRecord) -> None:
        TenantDatabase.objects.filter(id=record.id).update(
            host=record.host,
            port=record.port,
            name=record.name,
            db_username=record.db_username,
            secret_ref=record.secret_ref,
            tls_required=record.tls_required,
            status=record.status.value,
            schema_version=record.schema_version,
            last_health_at=record.last_health_at,
        )


class DjangoProvisioningJobRepository:
    def get(self, job_id: uuid.UUID) -> ProvisioningJobRecord | None:
        row = TenantProvisioningJob.objects.filter(id=job_id).first()
        return self._to_record(row) if row else None

    def get_open_for_tenant(self, tenant_id: uuid.UUID) -> ProvisioningJobRecord | None:
        row = (
            TenantProvisioningJob.objects.filter(tenant_id=tenant_id)
            .exclude(step__in=["ready", "failed"])
            .order_by("-created_at")
            .first()
        )
        if row is None:
            row = (
                TenantProvisioningJob.objects.filter(tenant_id=tenant_id, step="failed")
                .order_by("-created_at")
                .first()
            )
        return self._to_record(row) if row else None

    def create(self, job: ProvisioningJobRecord) -> None:
        TenantProvisioningJob.objects.create(
            id=job.id,
            tenant_id=job.tenant_id,
            step=job.step.value,
            attempts=job.attempts,
            last_error=job.last_error,
        )

    def update(self, job: ProvisioningJobRecord) -> None:
        TenantProvisioningJob.objects.filter(id=job.id).update(
            step=job.step.value,
            attempts=job.attempts,
            last_error=job.last_error,
        )

    def _to_record(self, row: TenantProvisioningJob) -> ProvisioningJobRecord:
        return ProvisioningJobRecord(
            id=row.id,
            tenant_id=row.tenant_id,
            step=ProvisioningStep(row.step),
            attempts=row.attempts,
            last_error=row.last_error,
        )


class DjangoMigrationJobRepository:
    def get(self, job_id: uuid.UUID) -> MigrationJobRecord | None:
        row = TenantMigrationJob.objects.filter(id=job_id).first()
        return self._to_record(row) if row else None

    def get_active_for_tenant(self, tenant_id: uuid.UUID) -> MigrationJobRecord | None:
        row = TenantMigrationJob.objects.filter(
            tenant_id=tenant_id, status__in=["pending", "locked", "running"]
        ).first()
        return self._to_record(row) if row else None

    def create(self, job: MigrationJobRecord) -> None:
        TenantMigrationJob.objects.create(
            id=job.id,
            tenant_id=job.tenant_id,
            source_version=job.source_version,
            target_version=job.target_version,
            status=job.status.value,
            canary=job.canary,
            last_error=job.last_error,
        )

    def update(self, job: MigrationJobRecord) -> None:
        TenantMigrationJob.objects.filter(id=job.id).update(
            source_version=job.source_version,
            target_version=job.target_version,
            status=job.status.value,
            canary=job.canary,
            last_error=job.last_error,
        )

    def _to_record(self, row: TenantMigrationJob) -> MigrationJobRecord:
        return MigrationJobRecord(
            id=row.id,
            tenant_id=row.tenant_id,
            source_version=row.source_version,
            target_version=row.target_version,
            status=MigrationJobStatus(row.status),
            canary=row.canary,
            last_error=row.last_error,
        )
