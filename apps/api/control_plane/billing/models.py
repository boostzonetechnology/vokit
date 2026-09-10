from __future__ import annotations

from django.db import models

from shared_kernel.ids import new_uuid7


class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    name = models.CharField(max_length=128)
    status = models.CharField(max_length=32, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_plans"


class PlanVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="versions")
    version = models.PositiveIntegerField()
    price_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    included_minutes = models.PositiveIntegerField()
    allow_topups = models.BooleanField(default=False)
    topup_minutes = models.PositiveIntegerField(default=0)
    topup_price_minor = models.BigIntegerField(default=0)
    overage_enabled = models.BooleanField(default=False)
    overage_price_per_minute_minor = models.BigIntegerField(default=0)
    grace_seconds = models.PositiveIntegerField(default=0)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_plan_versions"
        unique_together = (("plan", "version"),)


class InvoiceIndex(models.Model):
    invoice_id = models.UUIDField(primary_key=True)
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField()
    status = models.CharField(max_length=32)
    total_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "billing_invoice_index"
        indexes = [
            models.Index(fields=["tenant_id", "customer_id"], name="idx_inv_idx_tenant"),
        ]


class PaymentProcessorEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    processor = models.CharField(max_length=32)
    event_id = models.CharField(max_length=128)
    invoice_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=32, default="received")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_processor_events"
        unique_together = (("processor", "event_id"),)


class BillingSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    stripe_webhook_secret_ref = models.CharField(
        max_length=128, default="STRIPE_WEBHOOK_SECRET"
    )
    braintree_webhook_secret_ref = models.CharField(
        max_length=128, default="BRAINTREE_WEBHOOK_SECRET"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_settings"


class BillingIdempotencyKey(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    actor_id = models.UUIDField()
    key = models.CharField(max_length=128)
    kind = models.CharField(max_length=32)
    resource_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_idempotency_keys"
        unique_together = (("actor_id", "key"),)
