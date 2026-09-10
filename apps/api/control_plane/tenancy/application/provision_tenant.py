from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.tenancy.application.ports import (
    Clock,
    ProvisioningJobRecord,
    ProvisioningJobRepository,
    TenantDatabaseRecord,
    TenantDatabaseRepository,
    TenantRecord,
    TenantRepository,
)
from control_plane.tenancy.domain.types import (
    DatabaseStatus,
    ProvisioningStep,
    TenantStatus,
)
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.runtime.ports import (
    DatabaseAdministrator,
    SchemaRunner,
    TenantConnectionFactory,
    target_from_record,
)
from tenant.schema import CURRENT_VERSION

logger = logging.getLogger("vokit.tenancy")


@dataclass(frozen=True, slots=True)
class ProvisionTenantCommand:
    display_name: str
    host: str
    port: int
    name: str
    secret_ref: str
    tls_required: bool
    tenant_id: uuid.UUID | None = None


class ProvisionTenant:
    def __init__(
        self,
        tenants: TenantRepository,
        databases: TenantDatabaseRepository,
        jobs: ProvisioningJobRepository,
        admin: DatabaseAdministrator,
        connections: TenantConnectionFactory,
        schema: SchemaRunner,
        clock: Clock,
    ) -> None:
        self._tenants = tenants
        self._databases = databases
        self._jobs = jobs
        self._admin = admin
        self._connections = connections
        self._schema = schema
        self._clock = clock

    def execute(self, command: ProvisionTenantCommand) -> TenantRecord:
        self._validate(command)
        tenant_id = command.tenant_id or new_uuid7()
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            tenant = TenantRecord(
                id=tenant_id,
                display_name=command.display_name.strip(),
                status=TenantStatus.PROVISIONING,
            )
            self._tenants.create(tenant)
        job = self._jobs.get_open_for_tenant(tenant_id)
        if job is None:
            job = ProvisioningJobRecord(
                id=new_uuid7(),
                tenant_id=tenant_id,
                step=ProvisioningStep.CREATED,
                attempts=0,
                last_error="",
            )
            self._jobs.create(job)
        database = self._databases.get_for_tenant(tenant_id)
        if database is None:
            database = TenantDatabaseRecord(
                id=new_uuid7(),
                tenant_id=tenant_id,
                host=command.host.strip(),
                port=command.port,
                name=command.name.strip(),
                secret_ref=command.secret_ref.strip(),
                tls_required=command.tls_required,
                status=DatabaseStatus.ALLOCATING,
                schema_version="",
            )
            self._databases.create(database)
        return self.resume(tenant_id)

    def resume(self, tenant_id: uuid.UUID) -> TenantRecord:
        tenant = self._tenants.get(tenant_id)
        if tenant is not None and tenant.status is TenantStatus.READY:
            return tenant
        job = self._jobs.get_open_for_tenant(tenant_id)
        database = self._databases.get_for_tenant(tenant_id)
        if tenant is None or job is None or database is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        try:
            job = self._advance(job, ProvisioningStep.CREATED)
            target = target_from_record(database)
            self._admin.ensure_database(target)
            job = self._advance(job, ProvisioningStep.DATABASE_ALLOCATED)
            connection = self._connections.open(target)
            try:
                version = self._schema.apply(connection, CURRENT_VERSION)
                job = self._advance(job, ProvisioningStep.SCHEMA_APPLIED)
                self._schema.verify(connection, CURRENT_VERSION)
                database = TenantDatabaseRecord(
                    id=database.id,
                    tenant_id=database.tenant_id,
                    host=database.host,
                    port=database.port,
                    name=database.name,
                    secret_ref=database.secret_ref,
                    tls_required=database.tls_required,
                    status=DatabaseStatus.HEALTHY,
                    schema_version=version,
                    last_health_at=self._clock.now(),
                )
                self._databases.update(database)
                job = self._advance(job, ProvisioningStep.VERIFIED)
            finally:
                self._connections.close(connection)
            self._tenants.update_status(tenant_id, TenantStatus.READY)
            job = ProvisioningJobRecord(
                id=job.id,
                tenant_id=job.tenant_id,
                step=ProvisioningStep.READY,
                attempts=job.attempts + 1,
                last_error="",
            )
            self._jobs.update(job)
            log_event(
                logger,
                "tenant.provision.ready",
                outcome="success",
                tenant_id=str(tenant_id),
            )
            return self._tenants.get(tenant_id) or tenant
        except DomainError as exc:
            self._fail(tenant_id, job, str(exc.message))
            raise
        except Exception as exc:
            self._fail(tenant_id, job, "Provisioning failed.")
            raise DomainError(
                "tenant_provision_failed",
                "Provisioning failed.",
                http_status=503,
            ) from exc

    def _advance(
        self, job: ProvisioningJobRecord, step: ProvisioningStep
    ) -> ProvisioningJobRecord:
        if job.step in {ProvisioningStep.READY, ProvisioningStep.FAILED}:
            if job.step is ProvisioningStep.FAILED:
                updated = ProvisioningJobRecord(
                    id=job.id,
                    tenant_id=job.tenant_id,
                    step=step,
                    attempts=job.attempts,
                    last_error="",
                )
                self._jobs.update(updated)
                return updated
            return job
        order = [
            ProvisioningStep.CREATED,
            ProvisioningStep.DATABASE_ALLOCATED,
            ProvisioningStep.SCHEMA_APPLIED,
            ProvisioningStep.VERIFIED,
            ProvisioningStep.READY,
        ]
        if order.index(job.step) >= order.index(step):
            return job
        updated = ProvisioningJobRecord(
            id=job.id,
            tenant_id=job.tenant_id,
            step=step,
            attempts=job.attempts,
            last_error="",
        )
        self._jobs.update(updated)
        log_event(
            logger,
            "tenant.provision.step",
            outcome="success",
            tenant_id=str(job.tenant_id),
            step=step.value,
        )
        return updated

    def _fail(self, tenant_id: uuid.UUID, job: ProvisioningJobRecord, message: str) -> None:
        self._tenants.update_status(tenant_id, TenantStatus.FAILED)
        self._jobs.update(
            ProvisioningJobRecord(
                id=job.id,
                tenant_id=job.tenant_id,
                step=ProvisioningStep.FAILED,
                attempts=job.attempts + 1,
                last_error=message[:500],
            )
        )
        log_event(
            logger,
            "tenant.provision.failed",
            severity="error",
            outcome="error",
            tenant_id=str(tenant_id),
        )

    def _validate(self, command: ProvisionTenantCommand) -> None:
        if not command.display_name.strip():
            raise DomainError("validation_error", "display_name is required.")
        if not command.host.strip() or not command.name.strip():
            raise DomainError("validation_error", "Database host and name are required.")
        if command.port < 1 or command.port > 65535:
            raise DomainError("validation_error", "Database port is invalid.")
        if not command.secret_ref.strip() or any(ch.isspace() for ch in command.secret_ref):
            raise DomainError("validation_error", "secret_ref is invalid.")
