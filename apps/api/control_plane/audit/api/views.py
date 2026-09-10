from __future__ import annotations

from datetime import datetime

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.audit.application.ports import AuditSearchQuery
from control_plane.audit.domain.types import AuditSeverity
from control_plane.audit.infrastructure.container import search_audit
from control_plane.identity.api.auth import parse_optional_uuid, require_principal
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page


def _require_platform_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.PLATFORM)
    if permission not in context.permissions:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _parse_time(raw: object, field: str) -> datetime | None:
    if raw in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(raw))
    except ValueError as exc:
        raise DomainError("validation_error", f"{field} is invalid.") from exc


class PlatformAuditCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "audit.view")
        severity_raw = str(request.query_params.get("severity") or "").strip()
        severity = None
        if severity_raw:
            try:
                severity = AuditSeverity(severity_raw)
            except ValueError as exc:
                raise DomainError("validation_error", "severity is invalid.") from exc
        rows = search_audit().execute(
            AuditSearchQuery(
                actor_id=parse_optional_uuid(
                    request.query_params.get("actor_id"), field="actor_id"
                ),
                action=str(request.query_params.get("action") or "").strip(),
                entity_type=str(request.query_params.get("entity_type") or "").strip(),
                entity_id=str(request.query_params.get("entity_id") or "").strip(),
                tenant_id=parse_optional_uuid(
                    request.query_params.get("agency_id") or request.query_params.get("tenant_id"),
                    field="tenant_id",
                ),
                customer_id=parse_optional_uuid(
                    request.query_params.get("customer_id"), field="customer_id"
                ),
                ip=str(request.query_params.get("ip") or "").strip(),
                severity=severity,
                since=_parse_time(request.query_params.get("since"), "since"),
                until=_parse_time(request.query_params.get("until"), "until"),
            )
        )
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        sliced, page = page_slice(rows, offset, limit)
        return success(
            [
                {
                    "id": str(row.id),
                    "actor_id": str(row.actor_id) if row.actor_id else None,
                    "actor_role": row.actor_role,
                    "tenant_id": str(row.tenant_id) if row.tenant_id else None,
                    "customer_id": str(row.customer_id) if row.customer_id else None,
                    "action": row.action,
                    "entity_type": row.entity_type,
                    "entity_id": row.entity_id,
                    "severity": row.severity.value,
                    "correlation_id": row.correlation_id,
                    "ip": row.ip,
                    "reason": row.reason,
                    "before_summary": row.before_summary,
                    "after_summary": row.after_summary,
                    "payload": row.payload,
                    "created_at": row.created_at.isoformat(),
                }
                for row in sliced
            ],
            page=page,
        )


class PlatformAuditMutationView(CsrfAPIView):
    def patch(self, request: Request, event_id: str) -> Response:  # noqa: ARG002
        _require_platform_perm(request, "audit.view")
        raise DomainError(
            "audit_immutable",
            "Audit events cannot be edited or deleted.",
            http_status=409,
        )

    def delete(self, request: Request, event_id: str) -> Response:  # noqa: ARG002
        _require_platform_perm(request, "audit.view")
        raise DomainError(
            "audit_immutable",
            "Audit events cannot be edited or deleted.",
            http_status=409,
        )
