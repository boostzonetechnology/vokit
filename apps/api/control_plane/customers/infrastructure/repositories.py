from __future__ import annotations

import uuid
from datetime import datetime

from django.utils import timezone

from control_plane.customers.application.ports import UNSET, CustomerIndexRecord
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
        updated_at=row.updated_at,
        plan_id=row.plan_id,
        remaining_minutes=int(row.remaining_minutes),
        payment_due=bool(row.payment_due),
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
        plan_id: uuid.UUID | None = None,
        payment_due: bool | None = None,
        remaining_minutes_max: int | None = None,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> list[CustomerIndexRecord]:
        rows = CustomerIndex.objects.order_by("created_at")
        if tenant_id is not None:
            rows = rows.filter(tenant_id=tenant_id)
        if status is not None:
            rows = rows.filter(status=status.value)
        needle = query.strip()
        if needle:
            rows = rows.filter(display_name__icontains=needle[:128])
        if plan_id is not None:
            rows = rows.filter(plan_id=plan_id)
        if payment_due is not None:
            rows = rows.filter(payment_due=payment_due)
        if remaining_minutes_max is not None:
            rows = rows.filter(remaining_minutes__lte=remaining_minutes_max)
        if updated_after is not None:
            rows = rows.filter(updated_at__gte=updated_after)
        if updated_before is not None:
            rows = rows.filter(updated_at__lte=updated_before)
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
            updated_at=timezone.now(),
        )

    def project(
        self,
        customer_id: uuid.UUID,
        *,
        plan_id: object = UNSET,
        remaining_minutes: object = UNSET,
        payment_due: object = UNSET,
    ) -> None:
        fields: dict[str, object] = {}
        if plan_id is not UNSET:
            fields["plan_id"] = plan_id
        if remaining_minutes is not UNSET:
            fields["remaining_minutes"] = remaining_minutes
        if payment_due is not UNSET:
            fields["payment_due"] = payment_due
        if fields:
            CustomerIndex.objects.filter(id=customer_id).update(**fields)


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
