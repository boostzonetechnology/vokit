"""Shared tenant-DB credentials for API tests (memory runtime)."""

from __future__ import annotations

import hashlib
import uuid

TENANT_DB_TEST_PASSWORD = "TenantDbPass12!"


def tenant_db_payload(owner_email: str, *, host: str = "127.0.0.1", port: int = 3306) -> dict:
    digest = hashlib.sha256(owner_email.strip().lower().encode()).hexdigest()[:20]
    return {
        "host": host,
        "port": port,
        "username": f"u_{digest}",
        "password": TENANT_DB_TEST_PASSWORD,
    }


def unique_owner_email(prefix: str = "cust") -> str:
    cleaned = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in prefix.lower())[:24]
    return f"{cleaned or 'cust'}-{uuid.uuid4().hex[:12]}@vokit.test"


def platform_customer_body(
    agency_id: str | uuid.UUID,
    display_name: str,
    *,
    owner_email: str | None = None,
    **extra,
) -> dict:
    body = {
        "display_name": display_name,
        "agency_id": str(agency_id),
        "owner_email": owner_email or unique_owner_email(display_name),
    }
    body.update(extra)
    return body
