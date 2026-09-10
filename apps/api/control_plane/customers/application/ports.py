from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.customers.domain.policies import BanKey
from control_plane.customers.domain.types import CustomerStatus


@dataclass(frozen=True, slots=True)
class CustomerIndexRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    display_name: str
    status: CustomerStatus
    created_at: datetime | None = None


class CustomerIndexRepository(Protocol):
    def get(self, customer_id: uuid.UUID) -> CustomerIndexRecord | None: ...

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        status: CustomerStatus | None = None,
        query: str = "",
    ) -> list[CustomerIndexRecord]: ...

    def create(self, record: CustomerIndexRecord) -> None: ...

    def update(self, record: CustomerIndexRecord) -> None: ...


class BanIndex(Protocol):
    def is_banned(self, keys: list[BanKey]) -> bool: ...

    def add(self, key: BanKey) -> None: ...
