"""Shared tenant-DB credentials for API tests (memory runtime)."""

from __future__ import annotations

import hashlib

TENANT_DB_TEST_PASSWORD = "TenantDbPass12!"


def tenant_db_payload(owner_email: str, *, host: str = "127.0.0.1", port: int = 3306) -> dict:
    digest = hashlib.sha256(owner_email.strip().lower().encode()).hexdigest()[:20]
    return {
        "host": host,
        "port": port,
        "username": f"u_{digest}",
        "password": TENANT_DB_TEST_PASSWORD,
    }
