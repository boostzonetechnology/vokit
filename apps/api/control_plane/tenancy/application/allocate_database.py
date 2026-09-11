"""Server-side tenant database allocation (browser never chooses DB name)."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from django.conf import settings

from shared_kernel.errors import DomainError

VAULT_SECRET_REF = "vault:tenant_db"
_HOST_RE = re.compile(r"^[A-Za-z0-9._:-]+$")


@dataclass(frozen=True, slots=True)
class AllocatedDatabase:
    host: str
    port: int
    name: str
    db_username: str
    db_password: str
    tls_required: bool
    secret_ref: str = VAULT_SECRET_REF


def tenant_database_name(tenant_id: uuid.UUID) -> str:
    """Stable MySQL schema name derived from immutable tenant_id (max 64 chars)."""
    return f"vokit_t_{tenant_id.hex}"


def assert_mysql_ident(value: str, *, field: str = "username") -> str:
    cleaned = (value or "").strip()
    if not cleaned or any(ch in cleaned for ch in "`;/\\ \n\r\t"):
        raise DomainError("validation_error", f"{field} is invalid.")
    if len(cleaned) > 128:
        raise DomainError("validation_error", f"{field} is invalid.")
    return cleaned


def allocate_tenant_database(
    tenant_id: uuid.UUID,
    *,
    db_username: str,
    db_password: str,
    db_host: str | None = None,
    db_port: int | None = None,
    name_override: str | None = None,
) -> AllocatedDatabase:
    """
    Build registry coordinates. Host/port may come from Super Admin or settings.
    Password is returned only to the provisioner for vault storage — never HTTP.
    ``name_override`` is for management seeds only, never HTTP.
    """
    host = (db_host or "").strip() or str(getattr(settings, "TENANT_DB_HOST", "") or "").strip()
    port = int(db_port) if db_port is not None else int(getattr(settings, "TENANT_DB_PORT", 0) or 0)
    tls_required = bool(getattr(settings, "TENANT_TLS_REQUIRED", False))
    username = assert_mysql_ident(db_username, field="username")
    password = (db_password or "").strip()
    if len(password) < 12:
        raise DomainError("validation_error", "password must be at least 12 characters.")
    if not host:
        raise DomainError(
            "tenant_db_misconfigured",
            "Tenant database host is not configured.",
            http_status=503,
        )
    if not _HOST_RE.match(host):
        raise DomainError("validation_error", "host is invalid.")
    if port <= 0 or port > 65535:
        raise DomainError(
            "tenant_db_misconfigured",
            "Tenant database port is not configured.",
            http_status=503,
        )
    name = (name_override or "").strip() or tenant_database_name(tenant_id)
    if not name or any(ch.isspace() for ch in name) or len(name) > 64:
        raise DomainError(
            "tenant_db_misconfigured",
            "Allocated database name is invalid.",
            http_status=503,
        )
    assert_mysql_ident(name, field="name")
    return AllocatedDatabase(
        host=host,
        port=port,
        name=name,
        db_username=username,
        db_password=password,
        tls_required=tls_required,
        secret_ref=VAULT_SECRET_REF,
    )
