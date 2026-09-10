from __future__ import annotations

from django.db import models

from shared_kernel.ids import new_uuid7


class CustomerIndex(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    tenant = models.ForeignKey(
        "tenancy.Tenant",
        on_delete=models.PROTECT,
        related_name="customer_index_rows",
    )
    display_name = models.CharField(max_length=255)
    status = models.CharField(max_length=32, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customer_index"


class BannedCustomerKey(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    kind = models.CharField(max_length=32)
    key_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "banned_customer_index"
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "key_hash"],
                name="customers_ban_key_unique",
            )
        ]
