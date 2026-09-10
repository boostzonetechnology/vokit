from __future__ import annotations

from django.db import models

from shared_kernel.ids import new_uuid7


class KycSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    provider_slug = models.CharField(max_length=32, default="external")
    api_key_ref = models.CharField(max_length=128, default="KYC_API_KEY")
    webhook_secret_ref = models.CharField(max_length=128, default="KYC_WEBHOOK_SECRET")
    hosted_base_url = models.CharField(max_length=255, default="https://kyc.example.test")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "kyc_settings"


class KycCase(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    tenant = models.OneToOneField(
        "tenancy.Tenant",
        on_delete=models.PROTECT,
        related_name="kyc_case",
    )
    status = models.CharField(max_length=32, default="not_started")
    provider_slug = models.CharField(max_length=32, default="external")
    session_id = models.CharField(max_length=128, blank=True, default="")
    inquiry_id = models.CharField(max_length=128, blank=True, default="")
    last_event_id = models.CharField(max_length=128, blank=True, default="")
    reason_code = models.CharField(max_length=64, blank=True, default="")
    external_note = models.CharField(max_length=255, blank=True, default="")
    internal_note = models.CharField(max_length=255, blank=True, default="")
    frozen = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "kyc_cases"


class KycProviderEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    event_id = models.CharField(max_length=128, unique=True)
    case = models.ForeignKey(
        KycCase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    mapped_status = models.CharField(max_length=32, blank=True, default="")
    reason_code = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(max_length=32, default="received")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "kyc_provider_events"
