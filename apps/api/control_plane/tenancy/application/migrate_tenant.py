from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.tenancy.application.ports import (
    Clock,
    MigrationJobRecord,
    MigrationJobRepository,
    TenantDatabaseRecord,
    TenantDatabaseRepository,
    TenantRepository,
)
from control_plane.tenancy.domain.policies import tenant_unavailable
from control_plane.tenancy.domain.types import (
    DatabaseStatus,
    MigrationJobStatus,
    TenantStatus,
)
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.runtime.ports import (
    SchemaRunner,
    TenantConnectionFactory,
    target_from_record,
)
from tenant.schema import CURRENT_VERSION, VERSION_ORDER

logger = logging.getLogger("vokit.tenancy")


@dataclass(frozen=True, slots=True)
class MigrateTenantCommand:
    tenant_id: uuid.UUID
    target_version: str = CURRENT_VERSION
    canary: bool = False


class MigrateTenant:
    def __init__(
        self,
        tenants: TenantRepository,
        databases: TenantDatabaseRepository,
        jobs: MigrationJobRepository,
        connections: TenantConnectionFactory,
        schema: SchemaRunner,
        clock: Clock,
    ) -> None:
        self._tenants = tenants
        self._databases = databases
        self._jobs = jobs
        self._connections = connections
        self._schema = schema
        self._clock = clock

    def execute(self, command: MigrateTenantCommand) -> MigrationJobRecord:
        if command.target_version not in VERSION_ORDER:
            raise DomainError("validation_error", "Unknown tenant schema version.")
        tenant = self._tenants.get(command.tenant_id)
        database = self._databases.get_for_tenant(command.tenant_id)
        if tenant is None or database is None:
            raise tenant_unavailable()
        active = self._jobs.get_active_for_tenant(command.tenant_id)
        if active is not None:
            return self._run(active, database)
        job = MigrationJobRecord(
            id=new_uuid7(),
            tenant_id=command.tenant_id,
            source_version=database.schema_version,
            target_version=command.target_version,
            status=MigrationJobStatus.PENDING,
            canary=command.canary,
            last_error="",
        )
        self._jobs.create(job)
        return self._run(job, database)

    def _run(self, job: MigrationJobRecord, database: TenantDatabaseRecord) -> MigrationJobRecord:
        locked = self._with_status(job, MigrationJobStatus.LOCKED)
        self._tenants.update_status(job.tenant_id, TenantStatus.MIGRATING)
        running = self._with_status(locked, MigrationJobStatus.RUNNING)
        target = target_from_record(database)
        connection = None
        try:
            connection = self._connections.open(target)
            version = self._schema.apply(connection, job.target_version)
            self._schema.verify(connection, job.target_version)
            self._databases.update(
                TenantDatabaseRecord(
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
            )
            succeeded = self._with_status(running, MigrationJobStatus.SUCCEEDED)
            self._tenants.update_status(job.tenant_id, TenantStatus.READY)
            log_event(
                logger,
                "tenant.migration.completed",
                outcome="success",
                tenant_id=str(job.tenant_id),
                canary=job.canary,
                version=version,
            )
            return succeeded
        except Exception as exc:
            failed = MigrationJobRecord(
                id=running.id,
                tenant_id=running.tenant_id,
                source_version=running.source_version,
                target_version=running.target_version,
                status=MigrationJobStatus.FAILED,
                canary=running.canary,
                last_error="Migration failed.",
            )
            self._jobs.update(failed)
            self._tenants.update_status(job.tenant_id, TenantStatus.FAILED)
            log_event(
                logger,
                "tenant.migration.failed",
                severity="error",
                outcome="error",
                tenant_id=str(job.tenant_id),
                canary=job.canary,
            )
            raise DomainError(
                "tenant_migration_failed",
                "Migration failed.",
                http_status=503,
            ) from exc
        finally:
            if connection is not None:
                self._connections.close(connection)

    def _with_status(
        self, job: MigrationJobRecord, status: MigrationJobStatus
    ) -> MigrationJobRecord:
        updated = MigrationJobRecord(
            id=job.id,
            tenant_id=job.tenant_id,
            source_version=job.source_version,
            target_version=job.target_version,
            status=status,
            canary=job.canary,
            last_error=job.last_error,
        )
        self._jobs.update(updated)
        return updated


class MigrateTenantBatch:
    def __init__(self, migrate: MigrateTenant, *, concurrency: int) -> None:
        self._migrate = migrate
        self._concurrency = max(1, concurrency)

    def execute(
        self,
        tenant_ids: list[uuid.UUID],
        *,
        canary_ids: list[uuid.UUID],
        target_version: str = CURRENT_VERSION,
        canary_only: bool = False,
    ) -> list[MigrationJobRecord]:
        results: list[MigrationJobRecord] = []
        for tenant_id in canary_ids:
            results.append(
                self._migrate.execute(
                    MigrateTenantCommand(
                        tenant_id=tenant_id,
                        target_version=target_version,
                        canary=True,
                    )
                )
            )
        if canary_only:
            return results
        canary_set = set(canary_ids)
        remaining = [tid for tid in tenant_ids if tid not in canary_set]
        # Bounded batches; a failed canary already raised and stops the rest.
        for offset in range(0, len(remaining), self._concurrency):
            chunk = remaining[offset : offset + self._concurrency]
            for tenant_id in chunk:
                results.append(
                    self._migrate.execute(
                        MigrateTenantCommand(
                            tenant_id=tenant_id,
                            target_version=target_version,
                            canary=False,
                        )
                    )
                )
        return results
