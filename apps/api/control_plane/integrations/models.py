from __future__ import annotations

from django.db import models


class IntegrationConnectionIndex(models.Model):
    id = models.UUIDField(primary_key=True)
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField()
    provider = models.CharField(max_length=32)
    status = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "integration_connection_index"
        indexes = [
            models.Index(fields=["tenant_id", "customer_id"], name="idx_int_idx_customer"),
        ]


class WebhookEndpointIndex(models.Model):
    id = models.UUIDField(primary_key=True)
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField()
    status = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "webhook_endpoint_index"
        indexes = [
            models.Index(fields=["tenant_id", "customer_id"], name="idx_wh_idx_customer"),
        ]
