from __future__ import annotations

from django.conf import settings

from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.identity.infrastructure.container import invite_user
from control_plane.tenancy.application.backup import (
    BackupControlPlane,
    BackupTenant,
    RestoreTenant,
)
from control_plane.tenancy.application.change_agency import (
    ChangeAgencyCapabilities,
    ChangeAgencyStatus,
    SetCommissionRate,
    UpdateAgencyProfile,
)
from control_plane.tenancy.application.create_agency import CreateAgency
from control_plane.tenancy.application.migrate_tenant import (
    MigrateTenant,
    MigrateTenantBatch,
)
from control_plane.tenancy.application.provision_tenant import ProvisionTenant
from control_plane.tenancy.infrastructure.repositories import (
    DjangoMigrationJobRepository,
    DjangoProvisioningJobRepository,
    DjangoTenantDatabaseRepository,
    DjangoTenantRepository,
)
from tenant.lifecycle.service import TenantLifecycleService
from tenant.runtime.memory import MemoryRuntime
from tenant.runtime.mysql import MysqlRuntime
from tenant.runtime.records import IsolationRecordService
from tenant.runtime.router import TenantRouter

_memory_runtime: MemoryRuntime | None = None
_mysql_runtime: MysqlRuntime | None = None


def tenant_repo() -> DjangoTenantRepository:
    return DjangoTenantRepository()


def database_repo() -> DjangoTenantDatabaseRepository:
    return DjangoTenantDatabaseRepository()


def provisioning_jobs() -> DjangoProvisioningJobRepository:
    return DjangoProvisioningJobRepository()


def migration_jobs() -> DjangoMigrationJobRepository:
    return DjangoMigrationJobRepository()


def runtime() -> MemoryRuntime | MysqlRuntime:
    backend = getattr(settings, "TENANT_RUNTIME", "memory")
    if backend == "mysql":
        return _mysql()
    return _memory()


def _memory() -> MemoryRuntime:
    global _memory_runtime
    if _memory_runtime is None:
        _memory_runtime = MemoryRuntime(
            max_per_tenant=int(
                getattr(settings, "TENANT_POOL_MAX_PER_TENANT", 4)
            ),
            max_tenants=int(
                getattr(settings, "TENANT_POOL_MAX_ACTIVE_TENANTS", 16)
            ),
        )
    return _memory_runtime


def _mysql() -> MysqlRuntime:
    global _mysql_runtime
    if _mysql_runtime is None:
        _mysql_runtime = MysqlRuntime(
            user=getattr(settings, "TENANT_DB_USER", "vokit"),
            connect_timeout=int(
                getattr(settings, "TENANT_CONNECT_TIMEOUT_SECONDS", 5)
            ),
            max_per_tenant=int(
                getattr(settings, "TENANT_POOL_MAX_PER_TENANT", 4)
            ),
            max_tenants=int(
                getattr(settings, "TENANT_POOL_MAX_ACTIVE_TENANTS", 16)
            ),
        )
    return _mysql_runtime


def reset_runtime() -> None:
    global _memory_runtime, _mysql_runtime
    _memory_runtime = None
    _mysql_runtime = None


def router() -> TenantRouter:
    engine = runtime()
    return TenantRouter(tenant_repo(), database_repo(), engine)


def isolation_records() -> IsolationRecordService:
    engine = runtime()
    return IsolationRecordService(router(), engine)


def provisioner() -> ProvisionTenant:
    engine = runtime()
    return ProvisionTenant(
        tenant_repo(),
        database_repo(),
        provisioning_jobs(),
        engine,
        engine,
        engine,
        SystemClock(),
    )


def migrator() -> MigrateTenant:
    engine = runtime()
    return MigrateTenant(
        tenant_repo(),
        database_repo(),
        migration_jobs(),
        engine,
        engine,
        SystemClock(),
    )


def backup_tenant() -> BackupTenant:
    engine = runtime()
    return BackupTenant(tenant_repo(), database_repo(), engine)


def restore_tenant() -> RestoreTenant:
    engine = runtime()
    return RestoreTenant(tenant_repo(), database_repo(), engine)


def backup_control_plane() -> BackupControlPlane:
    return BackupControlPlane(tenant_repo(), database_repo())


def migration_batch() -> MigrateTenantBatch:
    return MigrateTenantBatch(
        migrator(),
        concurrency=int(
            getattr(settings, "TENANT_MIGRATION_CONCURRENCY", 2)
        ),
    )


def lifecycle() -> TenantLifecycleService:
    engine = runtime()
    return TenantLifecycleService(router(), engine)


def create_agency() -> CreateAgency:
    return CreateAgency(
        provisioner(),
        tenant_repo(),
        lifecycle(),
        invite_user(),
        SystemClock(),
    )


def change_agency_status() -> ChangeAgencyStatus:
    return ChangeAgencyStatus(tenant_repo(), lifecycle(), SystemClock())


def change_agency_capabilities() -> ChangeAgencyCapabilities:
    return ChangeAgencyCapabilities(tenant_repo(), lifecycle(), SystemClock())


def update_agency_profile() -> UpdateAgencyProfile:
    return UpdateAgencyProfile(tenant_repo(), lifecycle(), SystemClock())


def set_commission_rate() -> SetCommissionRate:
    return SetCommissionRate(tenant_repo(), SystemClock())
