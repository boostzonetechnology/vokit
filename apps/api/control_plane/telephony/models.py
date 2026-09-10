from __future__ import annotations

from django.db import models

from shared_kernel.ids import new_uuid7


class PhoneNumber(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    e164 = models.CharField(max_length=16, unique=True)
    country = models.CharField(max_length=8, default="US")
    area = models.CharField(max_length=16, blank=True, default="")
    capabilities = models.CharField(max_length=64, default="voice")
    provider = models.CharField(max_length=32, default="platform")
    provider_ref = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(max_length=32, default="available")
    monthly_cost_minor = models.BigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="USD")
    assigned_tenant_id = models.UUIDField(null=True, blank=True)
    assigned_customer_id = models.UUIDField(null=True, blank=True)
    assigned_agent_id = models.UUIDField(null=True, blank=True)
    reservation_id = models.UUIDField(null=True, blank=True)
    reserved_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "phone_numbers"
        indexes = [
            models.Index(fields=["status", "country"], name="idx_phone_status_country"),
        ]


class PhoneNumberReservation(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    number = models.ForeignKey(
        PhoneNumber, on_delete=models.PROTECT, related_name="reservations"
    )
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField()
    agent_id = models.UUIDField()
    status = models.CharField(max_length=32, default="active")
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "phone_number_reservations"
        indexes = [
            models.Index(fields=["number", "status"], name="idx_reserve_number_status"),
            models.Index(fields=["expires_at", "status"], name="idx_reserve_expiry"),
        ]


class CallIndex(models.Model):
    id = models.UUIDField(primary_key=True)
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField()
    agent_id = models.UUIDField()
    edge_call_id = models.CharField(max_length=128, unique=True)
    e164 = models.CharField(max_length=16)
    direction = models.CharField(max_length=16)
    status = models.CharField(max_length=32)
    transfer_status = models.CharField(max_length=32, default="idle")
    remote_e164 = models.CharField(max_length=16, blank=True, default="")
    transfer_destination_id = models.UUIDField(null=True, blank=True)
    voicemail_status = models.CharField(max_length=16, blank=True, default="")
    hunt_index = models.PositiveIntegerField(default=0)
    billed_minutes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "call_index"
        indexes = [
            models.Index(fields=["tenant_id", "customer_id"], name="idx_call_idx_tenant"),
        ]


class TransferDestinationIndex(models.Model):
    id = models.UUIDField(primary_key=True)
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField()
    kind = models.CharField(max_length=16)
    label = models.CharField(max_length=128)
    status = models.CharField(max_length=16, default="active")
    platform_disabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transfer_destination_index"
        indexes = [
            models.Index(fields=["tenant_id", "customer_id"], name="idx_xfer_idx_tenant"),
        ]


class TrainingSessionIndex(models.Model):
    session_id = models.UUIDField(primary_key=True)
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField()
    agent_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "training_session_index"


class TrainingProposal(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    session_id = models.UUIDField()
    kind = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    scope = models.CharField(max_length=32, blank=True, default="")
    status = models.CharField(max_length=16, default="proposed")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "training_proposals"
