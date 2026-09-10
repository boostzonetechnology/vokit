from __future__ import annotations

from django.db import models

from shared_kernel.ids import new_uuid7


class RecordingArtifactIndex(models.Model):
    id = models.UUIDField(primary_key=True)
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField()
    call_id = models.UUIDField()
    kind = models.CharField(max_length=32)
    object_key = models.CharField(max_length=255)
    checksum = models.CharField(max_length=80)
    status = models.CharField(max_length=16)
    legal_hold = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recording_artifact_index"
        indexes = [
            models.Index(fields=["tenant_id", "call_id"], name="idx_rec_idx_call"),
            models.Index(fields=["object_key"], name="idx_rec_idx_object"),
        ]


class RecordingIngestEvent(models.Model):
    event_id = models.CharField(max_length=128, primary_key=True)
    artifact_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recording_ingest_events"


class RecordingAccessGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    token_hash = models.CharField(max_length=64, unique=True)
    artifact_id = models.UUIDField()
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField()
    call_id = models.UUIDField()
    actor_id = models.UUIDField()
    status = models.CharField(max_length=16, default="issued")
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recording_access_grants"
        indexes = [
            models.Index(fields=["artifact_id", "status"], name="idx_rec_grant_artifact"),
        ]
