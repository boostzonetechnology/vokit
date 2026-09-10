"""Server-side tenant database allocation (browser never chooses host/DSN/name)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from django.conf import settings

from shared_kernel.errors import DomainError


@dataclass(frozen=True, slots=True)
class AllocatedDatabase:
    host: str
    port: int
    name: str
    secret_ref: str
    tls_required: bool


def tenant_database_name(tenant_id: uuid.UUID) -> str:
    """Stable MySQL schema name derived from immutable tenant_id (max 64 chars)."""
    return f"vokit_t_{tenant_id.hex}"


def allocate_tenant_database(
    tenant_id: uuid.UUID,
    *,
    name_override: str | None = None,
) -> AllocatedDatabase:
    """
    Build registry coordinates from trusted settings only.

    ``name_override`` is for management seeds (demo TENANT_DB_NAME_A/B), never HTTP.
    """
    host = str(getattr(settings, "TENANT_DB_HOST", "") or "").strip()
    port = int(getattr(settings, "TENANT_DB_PORT", 0) or 0)
    secret_ref = str(getattr(settings, "TENANT_DB_PASSWORD_REF", "") or "").strip()
    tls_required = bool(getattr(settings, "TENANT_TLS_REQUIRED", False))
    if not host:
        raise DomainError(
            "tenant_db_misconfigured",
            "Tenant database host is not configured.",
            http_status=503,
        )
    if port <= 0 or port > 65535:
        raise DomainError(
            "tenant_db_misconfigured",
            "Tenant database port is not configured.",
            http_status=503,
        )
    if not secret_ref or any(ch.isspace() for ch in secret_ref):
        raise DomainError(
            "tenant_db_misconfigured",
            "Tenant database secret reference is not configured.",
            http_status=503,
        )
    name = (name_override or "").strip() or tenant_database_name(tenant_id)
    if not name or any(ch.isspace() for ch in name) or len(name) > 64:
        raise DomainError(
            "tenant_db_misconfigured",
            "Allocated database name is invalid.",
            http_status=503,
        )
    return AllocatedDatabase(
        host=host,
        port=port,
        name=name,
        secret_ref=secret_ref,
        tls_required=tls_required,
    )
