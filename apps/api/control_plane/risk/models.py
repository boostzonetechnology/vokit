from __future__ import annotations

from django.db import models

from shared_kernel.ids import new_uuid7


class RiskCase(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField(unique=True)
    status = models.CharField(max_length=32, default="normal")
    last_invoice_id = models.UUIDField(null=True, blank=True)
    last_payment_id = models.UUIDField(null=True, blank=True)
    last_event_id = models.CharField(max_length=128, blank=True, default="")
    note = models.CharField(max_length=255, blank=True, default="")
    permanently_banned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "risk_cases"
        indexes = [
            models.Index(fields=["tenant_id", "status"], name="idx_risk_tenant_status"),
        ]


class RiskEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    processor = models.CharField(max_length=32)
    event_id = models.CharField(max_length=128)
    customer_id = models.UUIDField(null=True, blank=True)
    kind = models.CharField(max_length=32)
    status = models.CharField(max_length=32, default="received")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "risk_events"
        unique_together = (("processor", "event_id"),)


class VerificationSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    case = models.ForeignKey(
        RiskCase, on_delete=models.PROTECT, related_name="verifications"
    )
    status = models.CharField(max_length=32, default="submitted")
    id_object_ref = models.CharField(max_length=128)
    id_checksum = models.CharField(max_length=128)
    card_object_ref = models.CharField(max_length=128)
    card_checksum = models.CharField(max_length=128)
    card_last4 = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "risk_verifications"
