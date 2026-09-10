from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from control_plane.customers.domain.types import CustomerStatus
from control_plane.tenancy.domain.lifecycle import AgencyCapabilities, AgencyStatus


@dataclass(frozen=True, slots=True)
class AgencyProfile:
    tenant_id: uuid.UUID
    display_name: str
    legal_name: str
    status: AgencyStatus
    currency: str
    capabilities: AgencyCapabilities
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class TenantCustomer:
    customer_id: uuid.UUID
    tenant_id: uuid.UUID
    display_name: str
    status: CustomerStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None
