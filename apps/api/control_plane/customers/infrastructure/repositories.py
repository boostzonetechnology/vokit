from __future__ import annotations

import uuid

from control_plane.customers.application.ports import CustomerIndexRecord
from control_plane.customers.domain.policies import BanKey, hash_ban_key, normalize_ban_key
from control_plane.customers.domain.types import CustomerStatus
from control_plane.customers.models import BannedCustomerKey, CustomerIndex
from shared_kernel.ids import new_uuid7


def _index(row: CustomerIndex) -> CustomerIndexRecord:
    return CustomerIndexRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        display_name=row.display_name,
        status=CustomerStatus(row.status),
        created_at=row.created_at,
    )


class DjangoCustomerIndexRepository:
    def get(self, customer_id: uuid.UUID) -> CustomerIndexRecord | None:
        row = CustomerIndex.objects.filter(id=customer_id).first()
        return _index(row) if row else None

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        status: CustomerStatus | None = None,
        query: str = "",
    ) -> list[CustomerIndexRecord]:
        rows = CustomerIndex.objects.order_by("created_at")
        if tenant_id is not None:
            rows = rows.filter(tenant_id=tenant_id)
        if status is not None:
            rows = rows.filter(status=status.value)
        needle = query.strip()
        if needle:
            rows = rows.filter(display_name__icontains=needle[:128])
        return [_index(row) for row in rows]

    def create(self, record: CustomerIndexRecord) -> None:
        CustomerIndex.objects.create(
            id=record.id,
            tenant_id=record.tenant_id,
            display_name=record.display_name,
            status=record.status.value,
        )

    def update(self, record: CustomerIndexRecord) -> None:
        CustomerIndex.objects.filter(id=record.id).update(
            display_name=record.display_name,
            status=record.status.value,
        )


class DjangoBanIndex:
    def is_banned(self, keys: list[BanKey]) -> bool:
        if not keys:
            return False
        hashes = [(key.kind, hash_ban_key(key)) for key in keys]
        for kind, digest in hashes:
            if BannedCustomerKey.objects.filter(kind=kind, key_hash=digest).exists():
                return True
        return False

    def add(self, key: BanKey) -> None:
        normalized = normalize_ban_key(key)
        BannedCustomerKey.objects.get_or_create(
            kind=normalized.kind,
            key_hash=hash_ban_key(normalized),
            defaults={"id": new_uuid7()},
        )
