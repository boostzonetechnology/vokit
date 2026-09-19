from __future__ import annotations

from django.db import models

from shared_kernel.hard_delete import HardDeleteForbiddenModel
from shared_kernel.ids import new_uuid7


class WalletLock(models.Model):
    tenant_id = models.UUIDField(primary_key=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commission_wallet_locks"


class LedgerEntry(HardDeleteForbiddenModel):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField(null=True, blank=True)
    kind = models.CharField(max_length=32)
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    payment_id = models.UUIDField(null=True, blank=True)
    invoice_id = models.UUIDField(null=True, blank=True)
    commission_id = models.UUIDField(null=True, blank=True)
    payout_id = models.UUIDField(null=True, blank=True)
    eligible_base_minor = models.BigIntegerField(null=True, blank=True)
    rate_bps_snapshot = models.PositiveIntegerField(null=True, blank=True)
    earned_at = models.DateTimeField(null=True, blank=True)
    available_at = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True, default="")
    actor_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "commission_ledger_entries"
        indexes = [
            models.Index(fields=["tenant_id", "created_at"], name="idx_ledger_tenant"),
            models.Index(fields=["payment_id"], name="idx_ledger_payment"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "payment_id"],
                name="uq_ledger_kind_payment",
            ),
            models.UniqueConstraint(
                fields=["kind", "commission_id"],
                name="uq_ledger_kind_commission",
            ),
        ]


class Payout(HardDeleteForbiddenModel):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    tenant_id = models.UUIDField()
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=32)
    method_label = models.CharField(max_length=64, default="bank")
    transaction_ref = models.CharField(max_length=64, blank=True, default="")
    receipt_number = models.CharField(max_length=64, blank=True, default="")
    requested_by_id = models.UUIDField()
    decided_by_id = models.UUIDField(null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "commission_payouts"
        indexes = [
            models.Index(fields=["tenant_id", "status"], name="idx_payout_tenant"),
        ]


class AgencyPayoutMethod(HardDeleteForbiddenModel):
    """Agency bank/payout destination (AG11-004 / VKT-028)."""

    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    tenant_id = models.UUIDField()
    beneficiary_name = models.CharField(max_length=128)
    account_identifier = models.CharField(max_length=128)
    bank_name = models.CharField(max_length=128)
    country = models.CharField(max_length=2)
    currency = models.CharField(max_length=3, default="USD")
    label = models.CharField(max_length=64)
    status = models.CharField(max_length=16, default="pending")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commission_payout_methods"
        indexes = [
            models.Index(fields=["tenant_id", "status"], name="idx_payout_method_tenant"),
        ]


class PayoutProof(HardDeleteForbiddenModel):
    payout = models.OneToOneField(
        Payout,
        on_delete=models.PROTECT,
        related_name="proof",
        primary_key=True,
    )
    object_ref = models.CharField(max_length=255)
    content_type = models.CharField(max_length=128)
    checksum = models.CharField(max_length=128)
    uploaded_by_id = models.UUIDField()
    # TL exception to BR-009: per-payout share only (default private).
    agency_visible = models.BooleanField(default=False)
    agency_visible_at = models.DateTimeField(null=True, blank=True)
    agency_visible_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "commission_payout_proofs"


class CommissionIdempotencyKey(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    actor_id = models.UUIDField()
    key = models.CharField(max_length=128)
    resource_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "commission_idempotency_keys"
        unique_together = (("actor_id", "key"),)
