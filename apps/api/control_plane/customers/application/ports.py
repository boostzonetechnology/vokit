from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.customers.domain.policies import BanKey
from control_plane.customers.domain.types import CustomerStatus

UNSET = object()


@dataclass(frozen=True, slots=True)
class CustomerIndexRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    display_name: str
    status: CustomerStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None
    plan_id: uuid.UUID | None = None
    remaining_minutes: int = 0
    payment_due: bool = False


class CustomerIndexRepository(Protocol):
    def get(self, customer_id: uuid.UUID) -> CustomerIndexRecord | None: ...

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        status: CustomerStatus | None = None,
        query: str = "",
        plan_id: uuid.UUID | None = None,
        payment_due: bool | None = None,
        remaining_minutes_max: int | None = None,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> list[CustomerIndexRecord]: ...

    def create(self, record: CustomerIndexRecord) -> None: ...

    def update(self, record: CustomerIndexRecord) -> None: ...

    def project(
        self,
        customer_id: uuid.UUID,
        *,
        plan_id: object = UNSET,
        remaining_minutes: object = UNSET,
        payment_due: object = UNSET,
    ) -> None: ...


class BanIndex(Protocol):
    def is_banned(self, keys: list[BanKey]) -> bool: ...

    def add(self, key: BanKey) -> None: ...
