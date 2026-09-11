from __future__ import annotations

from enum import StrEnum


class TenantStatus(StrEnum):
    PROVISIONING = "provisioning"
    READY = "ready"
    DEGRADED = "degraded"
    MIGRATING = "migrating"
    SUSPENDED = "suspended"
    FAILED = "failed"
    DECOMMISSIONING = "decommissioning"


class DatabaseStatus(StrEnum):
    ALLOCATING = "allocating"
    VERIFYING = "verifying"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    SUSPENDED = "suspended"


class ProvisioningStep(StrEnum):
    CREATED = "created"
    DATABASE_ALLOCATED = "database_allocated"
    USER_CREATED = "user_created"
    SCHEMA_APPLIED = "schema_applied"
    VERIFIED = "verified"
    READY = "ready"
    FAILED = "failed"


class MigrationJobStatus(StrEnum):
    PENDING = "pending"
    LOCKED = "locked"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


ROUTABLE_TENANT_STATUSES = frozenset({TenantStatus.READY, TenantStatus.MIGRATING})
ROUTABLE_DATABASE_STATUSES = frozenset({DatabaseStatus.HEALTHY})
