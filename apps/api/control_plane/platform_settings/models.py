from __future__ import annotations

from django.db import models

from shared_kernel.ids import new_uuid7


class PlatformSetting(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    key = models.CharField(max_length=64, unique=True)
    value = models.JSONField()
    secret = models.BooleanField(default=False)
    updated_by_id = models.UUIDField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_settings"


class AgencyFeatureFlag(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    tenant_id = models.UUIDField()
    flag = models.CharField(max_length=32)
    enabled = models.BooleanField(default=True)
    updated_by_id = models.UUIDField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agency_feature_flags"
        constraints = [
            models.UniqueConstraint(fields=["tenant_id", "flag"], name="uniq_agency_flag")
        ]
