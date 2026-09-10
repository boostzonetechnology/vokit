from __future__ import annotations

import logging
import uuid

from celery import shared_task

from control_plane.tenancy.application.migrate_tenant import MigrateTenantCommand
from control_plane.tenancy.infrastructure.container import migrator, provisioner
from shared_kernel.http.correlation import set_correlation_id
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.tenancy")


@shared_task(name="tenancy.provision_tenant")
def provision_tenant_task(tenant_id: str, correlation_id: str) -> None:
    set_correlation_id(correlation_id)
    log_event(logger, "tenant.provision.job", tenant_id=tenant_id)
    provisioner().resume(uuid.UUID(tenant_id))


@shared_task(name="tenancy.migrate_tenant")
def migrate_tenant_task(tenant_id: str, target_version: str, correlation_id: str) -> None:
    set_correlation_id(correlation_id)
    log_event(logger, "tenant.migration.job", tenant_id=tenant_id)
    migrator().execute(
        MigrateTenantCommand(
            tenant_id=uuid.UUID(tenant_id),
            target_version=target_version,
        )
    )
