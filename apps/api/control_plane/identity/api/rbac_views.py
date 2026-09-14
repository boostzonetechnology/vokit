"""Platform RBAC role and permission APIs (SA18 / ADR-007)."""

from __future__ import annotations

import logging

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.identity.api.auth import (
    parse_uuid,
    require_agency_perm,
    require_customer_perm,
    require_platform_perm,
)
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.infrastructure.rbac_seed import ensure_rbac_seeded
from control_plane.identity.models import Permission, Role, RolePermission
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.identity")


def _perm_item(row: Permission) -> dict[str, object]:
    return {
        "id": str(row.id),
        "namespace": row.namespace,
        "code": row.code,
        "description": row.description,
        "is_sensitive": row.is_sensitive,
        "is_custom": getattr(row, "is_custom", False),
    }


def _role_item(row: Role, *, include_permissions: bool = True) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": str(row.id),
        "namespace": row.namespace,
        "slug": row.slug,
        "display_name": row.display_name,
        "is_system": row.is_system,
    }
    if include_permissions:
        codes = list(
            RolePermission.objects.filter(role_id=row.id)
            .select_related("permission")
            .values_list("permission__code", flat=True)
            .order_by("permission__code")
        )
        payload["permissions"] = codes
    return payload


class PlatformPermissionCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "permission.view")
        qs = Permission.objects.all().order_by("namespace", "code")
        namespace = request.query_params.get("namespace")
        module = request.query_params.get("module")
        if namespace:
            qs = qs.filter(namespace=str(namespace))
        if module:
            qs = qs.filter(code__startswith=f"{module}.")
        return success([_perm_item(row) for row in qs])

    def post(self, request: Request) -> Response:
        context = require_platform_perm(request, "permission.create")
        data = request.data if isinstance(request.data, dict) else {}
        namespace = str(data.get("namespace") or "").strip()
        code = str(data.get("code") or "").strip()
        description = str(data.get("description") or "").strip()
        if namespace not in {"platform", "agency", "customer"}:
            raise DomainError("validation_error", "namespace is invalid.")
        if "." not in code or code.startswith(".") or code.endswith("."):
            raise DomainError("validation_error", "code must look like module.action.")
        if Permission.objects.filter(namespace=namespace, code=code).exists():
            raise DomainError("conflict", "Permission already exists.", http_status=409)
        is_sensitive = bool(data.get("is_sensitive"))
        if is_sensitive and namespace != "platform" and code != "recording.hold":
            raise DomainError(
                "validation_error",
                "Sensitive permissions are platform-only (except recording.hold).",
            )
        row = Permission.objects.create(
            id=new_uuid7(),
            namespace=namespace,
            code=code,
            description=description,
            is_sensitive=is_sensitive,
            is_custom=True,
        )
        log_event(
            logger,
            "rbac.permission.created",
            actor_id=str(context.user.id),
            code=code,
            namespace=namespace,
        )
        return success(_perm_item(row), status=201)


class PlatformPermissionSyncView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        require_platform_perm(request, "permission.sync")
        ensure_rbac_seeded()
        return success(
            {
                "synced": True,
                "permission_count": Permission.objects.count(),
                "role_count": Role.objects.count(),
            }
        )


class PlatformRoleCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "role.view")
        qs = Role.objects.all().order_by("namespace", "slug")
        namespace = request.query_params.get("namespace")
        if namespace:
            qs = qs.filter(namespace=str(namespace))
        return success([_role_item(row) for row in qs])

    def post(self, request: Request) -> Response:
        context = require_platform_perm(request, "role.create")
        data = request.data if isinstance(request.data, dict) else {}
        namespace = str(data.get("namespace") or "platform").strip()
        if namespace != "platform":
            raise DomainError(
                "validation_error",
                "Only platform roles can be created in V1 (SA18).",
            )
        slug = str(data.get("slug") or "").strip()
        display_name = str(data.get("display_name") or slug).strip()
        if not slug:
            raise DomainError("validation_error", "slug is required.")
        if slug == "super_admin":
            raise DomainError("validation_error", "Cannot create reserved super_admin role.")
        if Role.objects.filter(slug=slug).exists():
            raise DomainError("conflict", "Role slug already exists.", http_status=409)
        permission_codes = data.get("permissions") or []
        if not isinstance(permission_codes, list):
            raise DomainError("validation_error", "permissions must be a list of codes.")
        role = Role.objects.create(
            id=new_uuid7(),
            namespace=namespace,
            slug=slug,
            display_name=display_name,
            is_system=False,
        )
        self._replace_permissions(role, [str(c) for c in permission_codes])
        log_event(logger,
            "rbac.role.created",
            actor_id=str(context.user.id),
            role_slug=slug,
        )
        return success(_role_item(role), status=201)

    @staticmethod
    def _replace_permissions(role: Role, codes: list[str]) -> None:
        RolePermission.objects.filter(role=role).delete()
        if not codes:
            return
        perms = list(Permission.objects.filter(namespace=role.namespace, code__in=codes))
        found = {p.code for p in perms}
        missing = set(codes) - found
        if missing:
            raise DomainError(
                "validation_error",
                f"Unknown or wrong-namespace permissions: {', '.join(sorted(missing))}",
            )
        for perm in perms:
            if perm.is_sensitive and role.namespace != "platform":
                raise DomainError(
                    "forbidden",
                    "Sensitive permissions cannot attach to non-platform roles.",
                    http_status=403,
                )
            RolePermission.objects.create(id=new_uuid7(), role=role, permission=perm)


class PlatformRoleDetailView(CsrfAPIView):
    def get(self, request: Request, role_id: str) -> Response:
        require_platform_perm(request, "role.view")
        role = Role.objects.filter(id=parse_uuid(role_id, field="role_id")).first()
        if role is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return success(_role_item(role))

    def patch(self, request: Request, role_id: str) -> Response:
        context = require_platform_perm(request, "role.update")
        role = Role.objects.filter(id=parse_uuid(role_id, field="role_id")).first()
        if role is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if role.slug == "super_admin":
            raise DomainError("forbidden", "Cannot modify super_admin role.", http_status=403)
        data = request.data if isinstance(request.data, dict) else {}
        if "display_name" in data:
            role.display_name = str(data.get("display_name") or role.display_name).strip()
            role.save(update_fields=["display_name"])
        if "permissions" in data:
            codes = data.get("permissions") or []
            if not isinstance(codes, list):
                raise DomainError("validation_error", "permissions must be a list of codes.")
            # Platform may edit agency/customer system role pivots in V1.
            PlatformRoleCollectionView._replace_permissions(role, [str(c) for c in codes])
        log_event(logger,
            "rbac.role.updated",
            actor_id=str(context.user.id),
            role_slug=role.slug,
        )
        return success(_role_item(role))

    def delete(self, request: Request, role_id: str) -> Response:
        context = require_platform_perm(request, "role.delete")
        role = Role.objects.filter(id=parse_uuid(role_id, field="role_id")).first()
        if role is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if role.is_system:
            raise DomainError("forbidden", "System roles cannot be deleted.", http_status=403)
        slug = role.slug
        role.delete()
        log_event(logger,
            "rbac.role.deleted",
            actor_id=str(context.user.id),
            role_slug=slug,
        )
        return success({"deleted": True})


class AgencyRoleListView(CsrfAPIView):
    """Read-only agency role catalog for invite dropdowns."""

    def get(self, request: Request) -> Response:
        require_agency_perm(request, "team.view")
        rows = Role.objects.filter(namespace="agency").order_by("slug")
        return success([_role_item(row) for row in rows])


class CustomerRoleListView(CsrfAPIView):
    """Read-only customer role catalog for invite dropdowns."""

    def get(self, request: Request) -> Response:
        require_customer_perm(request, "team.view")
        rows = Role.objects.filter(namespace="customer").order_by("slug")
        return success([_role_item(row) for row in rows])
