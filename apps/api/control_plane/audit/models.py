from __future__ import annotations

from django.db import models

from control_plane.audit.domain.policies import assert_immutable
from shared_kernel.ids import new_uuid7


class AuditQuerySet(models.QuerySet):
    def update(self, **kwargs):  # noqa: ARG002
        assert_immutable()

    def delete(self):
        assert_immutable()


class AuditManager(models.Manager):
    def get_queryset(self) -> AuditQuerySet:
        return AuditQuerySet(self.model, using=self._db)


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    actor_id = models.UUIDField(null=True, blank=True)
    actor_role = models.CharField(max_length=64, blank=True, default="")
    tenant_id = models.UUIDField(null=True, blank=True)
    customer_id = models.UUIDField(null=True, blank=True)
    action = models.CharField(max_length=64)
    entity_type = models.CharField(max_length=64)
    entity_id = models.CharField(max_length=64, blank=True, default="")
    severity = models.CharField(max_length=16)
    correlation_id = models.CharField(max_length=64, blank=True, default="")
    ip = models.CharField(max_length=64, blank=True, default="")
    user_agent = models.CharField(max_length=255, blank=True, default="")
    reason = models.CharField(max_length=255, blank=True, default="")
    before_summary = models.CharField(max_length=255, blank=True, default="")
    after_summary = models.CharField(max_length=255, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AuditManager()

    class Meta:
        db_table = "audit_events"
        indexes = [
            models.Index(fields=["action", "created_at"], name="idx_audit_action_time"),
            models.Index(fields=["tenant_id", "created_at"], name="idx_audit_tenant_time"),
            models.Index(fields=["actor_id", "created_at"], name="idx_audit_actor_time"),
            models.Index(fields=["entity_type", "entity_id"], name="idx_audit_entity"),
        ]

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            assert_immutable()
        if type(self).objects.filter(pk=self.pk).exists():
            assert_immutable()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> None:  # noqa: ARG002
        assert_immutable()
