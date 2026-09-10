from __future__ import annotations

from django.db import models

from shared_kernel.ids import new_uuid7


class AgentTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    name = models.CharField(max_length=128)
    industry = models.CharField(max_length=64, blank=True, default="")
    use_case = models.CharField(max_length=64, blank=True, default="")
    description = models.CharField(max_length=255, blank=True, default="")
    languages = models.CharField(max_length=128, blank=True, default="en")
    visibility = models.CharField(max_length=16, default="global")
    selected_tenant_ids = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=16, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "agent_templates"


class TemplateVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    template = models.ForeignKey(
        AgentTemplate, on_delete=models.PROTECT, related_name="versions"
    )
    version = models.PositiveIntegerField()
    agent_type = models.CharField(max_length=64, default="custom")
    instructions = models.TextField(blank=True, default="")
    voice_provider = models.CharField(max_length=64, blank=True, default="")
    voice_id = models.CharField(max_length=64, blank=True, default="")
    language = models.CharField(max_length=16, blank=True, default="en")
    tools = models.JSONField(default=list, blank=True)
    fallback_behavior = models.CharField(max_length=16, default="message")
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "agent_template_versions"
        unique_together = (("template", "version"),)


class GlobalInstruction(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    body = models.TextField()
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "global_instructions"


class GlobalKnowledgeSource(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    title = models.CharField(max_length=128)
    body = models.TextField()
    status = models.CharField(max_length=16, default="ready")
    group_id = models.CharField(max_length=128, default="global")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "global_knowledge_sources"


class AgentIndex(models.Model):
    id = models.UUIDField(primary_key=True)
    tenant_id = models.UUIDField()
    customer_id = models.UUIDField()
    display_name = models.CharField(max_length=128)
    status = models.CharField(max_length=32)
    agent_type = models.CharField(max_length=64, default="custom")
    published_version = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent_index"
        indexes = [
            models.Index(fields=["tenant_id", "customer_id"], name="idx_agent_idx_tenant"),
        ]
