from __future__ import annotations

from django.db import models

from shared_kernel.ids import new_uuid7


class NotificationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    event_type = models.CharField(max_length=64)
    channel = models.CharField(max_length=16)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_templates"
        constraints = [
            models.UniqueConstraint(
                fields=["event_type", "channel"],
                name="uniq_notification_template_channel",
            )
        ]


class InAppNotification(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    user_id = models.UUIDField()
    tenant_id = models.UUIDField(null=True, blank=True)
    customer_id = models.UUIDField(null=True, blank=True)
    event_type = models.CharField(max_length=64)
    category = models.CharField(max_length=32)
    title = models.CharField(max_length=255)
    body = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "in_app_notifications"
        indexes = [
            models.Index(fields=["user_id", "created_at"], name="idx_inapp_user_time"),
            models.Index(fields=["tenant_id", "user_id"], name="idx_inapp_tenant_user"),
        ]


class NotificationDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    user_id = models.UUIDField(null=True, blank=True)
    recipient_email = models.CharField(max_length=254)
    channel = models.CharField(max_length=16)
    event_type = models.CharField(max_length=64)
    status = models.CharField(max_length=16)
    error = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification_deliveries"
        indexes = [
            models.Index(fields=["event_type", "created_at"], name="idx_ndel_event_time"),
            models.Index(fields=["recipient_email", "created_at"], name="idx_ndel_email"),
        ]


class NotificationPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    scope = models.CharField(max_length=16)
    user_id = models.UUIDField(null=True, blank=True)
    tenant_id = models.UUIDField(null=True, blank=True)
    customer_id = models.UUIDField(null=True, blank=True)
    event_type = models.CharField(max_length=64)
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_preferences"
        indexes = [
            models.Index(fields=["scope", "tenant_id"], name="idx_npref_scope_tenant"),
            models.Index(fields=["user_id", "event_type"], name="idx_npref_user_event"),
        ]
