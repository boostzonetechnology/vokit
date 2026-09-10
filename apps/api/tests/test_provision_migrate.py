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


@pytest.mark.django_db
def test_provisioning_is_idempotent_and_ready_only_after_verify() -> None:
    first = provisioner().execute(
        ProvisionTenantCommand(
            display_name="Agency One",
            host="127.0.0.1",
            port=3306,
            name="prov_one",
            secret_ref="TENANT_DB_PASSWORD",
            tls_required=False,
        )
    )
    assert first.status is TenantStatus.READY
    second = provisioner().execute(
        ProvisionTenantCommand(
            display_name="Agency One",
            host="127.0.0.1",
            port=3306,
            name="prov_one",
            secret_ref="TENANT_DB_PASSWORD",
            tls_required=False,
            tenant_id=first.id,
        )
    )
    assert second.id == first.id
    assert second.status is TenantStatus.READY


@pytest.mark.django_db
def test_canary_migration_then_bounded_batch() -> None:
    one = provisioner().execute(
        ProvisionTenantCommand(
            display_name="Canary",
            host="127.0.0.1",
            port=3306,
            name="mig_canary",
            secret_ref="TENANT_DB_PASSWORD",
            tls_required=False,
        )
    )
    two = provisioner().execute(
        ProvisionTenantCommand(
            display_name="Follow",
            host="127.0.0.1",
            port=3306,
            name="mig_follow",
            secret_ref="TENANT_DB_PASSWORD",
            tls_required=False,
        )
    )
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
    tenant = provisioner().execute(
        ProvisionTenantCommand(
            display_name="Worker",
            host="127.0.0.1",
            port=3306,
            name="prov_worker",
            secret_ref="TENANT_DB_PASSWORD",
            tls_required=False,
        )
    )
    provision_tenant_task.run(str(tenant.id), "corr-phase3")
    assert tenant_repo().get(tenant.id).status is TenantStatus.READY


@pytest.mark.django_db
def test_single_tenant_migration_lock_path() -> None:
    tenant = provisioner().execute(
        ProvisionTenantCommand(
            display_name="Lock",
            host="127.0.0.1",
            port=3306,
            name="mig_lock",
            secret_ref="TENANT_DB_PASSWORD",
            tls_required=False,
        )
    )
    job = migrator().execute(MigrateTenantCommand(tenant_id=tenant.id))
    assert job.status is MigrationJobStatus.SUCCEEDED
    again = migrator().execute(MigrateTenantCommand(tenant_id=tenant.id))
    assert again.status is MigrationJobStatus.SUCCEEDED


@pytest.mark.django_db
def test_migration_failure_isolates_one_tenant() -> None:
    healthy = provisioner().execute(
        ProvisionTenantCommand(
            display_name="Healthy",
            host="127.0.0.1",
            port=3306,
            name="mig_ok",
            secret_ref="TENANT_DB_PASSWORD",
            tls_required=False,
        )
    )
    broken = provisioner().execute(
        ProvisionTenantCommand(
            display_name="Broken",
            host="127.0.0.1",
            port=3306,
            name="mig_down",
            secret_ref="TENANT_DB_PASSWORD",
            tls_required=False,
        )
    )
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
