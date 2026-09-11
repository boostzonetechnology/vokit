from __future__ import annotations

import pytest

from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.application.migrate_tenant import MigrateTenantCommand
from control_plane.tenancy.application.provision_tenant import ProvisionTenantCommand
from control_plane.tenancy.domain.types import MigrationJobStatus, TenantStatus
from control_plane.tenancy.infrastructure.container import (
    isolation_records,
    migration_batch,
    migrator,
    provisioner,
    runtime,
    tenant_repo,
)
from control_plane.tenancy.tasks import provision_tenant_task
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from tenant.runtime.memory import MemoryRuntime
from tenant.schema import CURRENT_VERSION


def _cmd(name: str, db_name: str, *, tenant_id=None) -> ProvisionTenantCommand:
    return ProvisionTenantCommand(
        display_name=name,
        host="127.0.0.1",
        port=3306,
        name=db_name,
        db_username=f"u_{db_name}",
        db_password="TenantDbPass12!",
        tls_required=False,
        tenant_id=tenant_id,
    )


@pytest.mark.django_db
def test_provisioning_is_idempotent_and_ready_only_after_verify() -> None:
    first = provisioner().execute(_cmd("Agency One", "prov_one"))
    assert first.status is TenantStatus.READY
    second = provisioner().execute(
        _cmd("Agency One", "prov_one", tenant_id=first.id)
    )
    assert second.id == first.id
    assert second.status is TenantStatus.READY


@pytest.mark.django_db
def test_canary_migration_then_bounded_batch() -> None:
    one = provisioner().execute(_cmd("Canary", "mig_canary"))
    two = provisioner().execute(_cmd("Follow", "mig_follow"))
    jobs = migration_batch().execute(
        [one.id, two.id],
        canary_ids=[one.id],
        target_version=CURRENT_VERSION,
    )
    assert jobs[0].canary is True
    assert jobs[0].status is MigrationJobStatus.SUCCEEDED
    assert jobs[1].canary is False
    assert jobs[1].status is MigrationJobStatus.SUCCEEDED
    canary_only = migration_batch().execute(
        [one.id, two.id],
        canary_ids=[one.id],
        target_version=CURRENT_VERSION,
        canary_only=True,
    )
    assert len(canary_only) == 1
    assert canary_only[0].canary is True


@pytest.mark.django_db
def test_worker_reconstructs_tenant_from_id_only() -> None:
    tenant = provisioner().execute(_cmd("Worker", "prov_worker"))
    provision_tenant_task.run(str(tenant.id), "corr-phase3")
    assert tenant_repo().get(tenant.id).status is TenantStatus.READY


@pytest.mark.django_db
def test_single_tenant_migration_lock_path() -> None:
    tenant = provisioner().execute(_cmd("Lock", "mig_lock"))
    job = migrator().execute(MigrateTenantCommand(tenant_id=tenant.id))
    assert job.status is MigrationJobStatus.SUCCEEDED
    again = migrator().execute(MigrateTenantCommand(tenant_id=tenant.id))
    assert again.status is MigrationJobStatus.SUCCEEDED


@pytest.mark.django_db
def test_migration_failure_isolates_one_tenant() -> None:
    healthy = provisioner().execute(_cmd("Healthy", "mig_ok"))
    broken = provisioner().execute(_cmd("Broken", "mig_down"))
    engine = runtime()
    assert isinstance(engine, MemoryRuntime)
    engine.mark_down("mig_down")
    with pytest.raises(DomainError) as exc:
        migrator().execute(MigrateTenantCommand(tenant_id=broken.id))
    assert exc.value.code == "tenant_migration_failed"
    assert tenant_repo().get(broken.id).status is TenantStatus.FAILED
    assert tenant_repo().get(healthy.id).status is TenantStatus.READY
    object_id = new_uuid7()
    stored = isolation_records().put(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=healthy.id,
        claimed_tenant_id=broken.id,
        permissions=frozenset(),
        object_id=object_id,
        payload="still-isolated",
    )
    assert stored.tenant_id == healthy.id
    assert stored.payload == "still-isolated"
