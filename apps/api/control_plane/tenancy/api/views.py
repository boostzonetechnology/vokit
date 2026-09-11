from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.identity.api.auth import (
    parse_optional_uuid,
    parse_uuid,
    require_principal,
)
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.application.migrate_tenant import MigrateTenantCommand
from control_plane.tenancy.application.ports import TenantDatabaseRecord, TenantRecord
from control_plane.tenancy.application.provision_tenant import ProvisionTenantCommand
from control_plane.tenancy.infrastructure.container import (
    database_repo,
    isolation_records,
    migration_batch,
    migrator,
    provisioner,
    tenant_repo,
)
from shared_kernel.errors import DomainError
from shared_kernel.http.correlation import get_correlation_id
from shared_kernel.http.envelope import success
from shared_kernel.ids import new_uuid7
from tenant.schema import CURRENT_VERSION


def _require_platform_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.PLATFORM)
    if permission not in context.permissions:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _tenant_payload(
    tenant: TenantRecord, database: TenantDatabaseRecord | None
) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": str(tenant.id),
        "display_name": tenant.display_name,
        "status": tenant.status.value,
    }
    if database is not None:
        payload["database"] = {
            "id": str(database.id),
            "host": database.host,
            "port": database.port,
            "name": database.name,
            "username": database.db_username,
            "tls_required": database.tls_required,
            "status": database.status.value,
            "schema_version": database.schema_version,
        }
    return payload


class TenantCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "tenants.view")
        rows = []
        for tenant in tenant_repo().list():
            mapped = database_repo().get_for_tenant(tenant.id)
            rows.append(_tenant_payload(tenant, mapped))
        return success(rows)

    def post(self, request: Request) -> Response:
        _require_platform_perm(request, "tenants.provision")
        database = request.data.get("database") or {}
        if "name" not in database:
            raise DomainError("validation_error", "database.name is required.")
        tenant = provisioner().execute(
            ProvisionTenantCommand(
                display_name=str(request.data.get("display_name") or ""),
                host=str(database.get("host") or ""),
                port=int(database.get("port") or 0),
                name=str(database.get("name") or ""),
                db_username=str(database.get("username") or ""),
                db_password=str(database.get("password") or ""),
                tls_required=bool(database.get("tls_required") or False),
                tenant_id=parse_optional_uuid(
                    request.data.get("tenant_id"), field="tenant_id"
                ),
            )
        )
        mapped = database_repo().get_for_tenant(tenant.id)
        return success(_tenant_payload(tenant, mapped), status=201)


class TenantDetailView(CsrfAPIView):
    def get(self, request: Request, tenant_id: str) -> Response:
        _require_platform_perm(request, "tenants.view")
        identifier = parse_uuid(tenant_id, field="tenant_id")
        tenant = tenant_repo().get(identifier)
        if tenant is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        mapped = database_repo().get_for_tenant(identifier)
        return success(_tenant_payload(tenant, mapped))


class TenantProvisionRetryView(CsrfAPIView):
    def post(self, request: Request, tenant_id: str) -> Response:
        _require_platform_perm(request, "tenants.provision")
        tenant = provisioner().resume(parse_uuid(tenant_id, field="tenant_id"))
        mapped = database_repo().get_for_tenant(tenant.id)
        return success(_tenant_payload(tenant, mapped))


class TenantMigrationView(CsrfAPIView):
    def post(self, request: Request, tenant_id: str) -> Response:
        _require_platform_perm(request, "tenants.migrate")
        job = migrator().execute(
            MigrateTenantCommand(
                tenant_id=parse_uuid(tenant_id, field="tenant_id"),
                target_version=str(
                    request.data.get("target_version") or CURRENT_VERSION
                ),
                canary=bool(request.data.get("canary") or False),
            )
        )
        return success(
            {
                "id": str(job.id),
                "tenant_id": str(job.tenant_id),
                "status": job.status.value,
                "source_version": job.source_version,
                "target_version": job.target_version,
                "canary": job.canary,
            }
        )


class TenantMigrationBatchView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        _require_platform_perm(request, "tenants.migrate")
        raw_ids = request.data.get("tenant_ids") or []
        raw_canary = request.data.get("canary_ids") or []
        tenant_ids = [parse_uuid(item, field="tenant_id") for item in raw_ids]
        canary_ids = [parse_uuid(item, field="canary_id") for item in raw_canary]
        jobs = migration_batch().execute(
            tenant_ids,
            canary_ids=canary_ids,
            target_version=str(
                request.data.get("target_version") or CURRENT_VERSION
            ),
        )
        return success(
            [
                {
                    "id": str(job.id),
                    "tenant_id": str(job.tenant_id),
                    "status": job.status.value,
                    "canary": job.canary,
                }
                for job in jobs
            ]
        )


class AgencyIsolationRecordView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.AGENCY)
        object_id = parse_optional_uuid(request.data.get("object_id"), field="object_id")
        if object_id is None:
            object_id = new_uuid7()
        claimed = parse_optional_uuid(request.data.get("tenant_id"), field="tenant_id")
        record = isolation_records().put(
            principal_type=context.membership.principal_type,
            membership_tenant_id=context.membership.tenant_id,
            claimed_tenant_id=claimed,
            permissions=context.permissions,
            object_id=object_id,
            payload=str(request.data.get("payload") or ""),
        )
        return success(
            {
                "object_id": str(record.object_id),
                "tenant_id": str(record.tenant_id),
                "payload": record.payload,
                "correlation_id": get_correlation_id(),
            },
            status=201,
        )


class AgencyIsolationRecordDetailView(CsrfAPIView):
    def get(self, request: Request, object_id: str) -> Response:
        context = require_principal(request, PrincipalType.AGENCY)
        record = isolation_records().get(
            principal_type=context.membership.principal_type,
            membership_tenant_id=context.membership.tenant_id,
            claimed_tenant_id=parse_optional_uuid(
                request.query_params.get("tenant_id"), field="tenant_id"
            ),
            permissions=context.permissions,
            object_id=parse_uuid(object_id, field="object_id"),
        )
        return success(
            {
                "object_id": str(record.object_id),
                "tenant_id": str(record.tenant_id),
                "payload": record.payload,
            }
        )
