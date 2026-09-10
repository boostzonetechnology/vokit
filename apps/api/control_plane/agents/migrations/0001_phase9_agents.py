import django.db.models.deletion
import shared_kernel.ids
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AgentTemplate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=shared_kernel.ids.new_uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=128)),
                ("industry", models.CharField(blank=True, default="", max_length=64)),
                ("use_case", models.CharField(blank=True, default="", max_length=64)),
                ("description", models.CharField(blank=True, default="", max_length=255)),
                ("languages", models.CharField(blank=True, default="en", max_length=128)),
                ("visibility", models.CharField(default="global", max_length=16)),
                ("selected_tenant_ids", models.JSONField(blank=True, default=list)),
                ("status", models.CharField(default="active", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "agent_templates"},
        ),
        migrations.CreateModel(
            name="GlobalInstruction",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=shared_kernel.ids.new_uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("body", models.TextField()),
                ("version", models.PositiveIntegerField(default=1)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "global_instructions"},
        ),
        migrations.CreateModel(
            name="GlobalKnowledgeSource",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=shared_kernel.ids.new_uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("title", models.CharField(max_length=128)),
                ("body", models.TextField()),
                ("status", models.CharField(default="ready", max_length=16)),
                ("group_id", models.CharField(default="global", max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "global_knowledge_sources"},
        ),
        migrations.CreateModel(
            name="AgentIndex",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField()),
                ("customer_id", models.UUIDField()),
                ("display_name", models.CharField(max_length=128)),
                ("status", models.CharField(max_length=32)),
                ("agent_type", models.CharField(default="custom", max_length=64)),
                ("published_version", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "agent_index"},
        ),
        migrations.CreateModel(
            name="TemplateVersion",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=shared_kernel.ids.new_uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("version", models.PositiveIntegerField()),
                ("agent_type", models.CharField(default="custom", max_length=64)),
                ("instructions", models.TextField(blank=True, default="")),
                ("voice_provider", models.CharField(blank=True, default="", max_length=64)),
                ("voice_id", models.CharField(blank=True, default="", max_length=64)),
                ("language", models.CharField(blank=True, default="en", max_length=16)),
                ("tools", models.JSONField(blank=True, default=list)),
                ("fallback_behavior", models.CharField(default="message", max_length=16)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "template",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="versions",
                        to="agents.agenttemplate",
                    ),
                ),
            ],
            options={
                "db_table": "agent_template_versions",
                "unique_together": {("template", "version")},
            },
        ),
        migrations.AddIndex(
            model_name="agentindex",
            index=models.Index(fields=["tenant_id", "customer_id"], name="idx_agent_idx_tenant"),
        ),
    ]
