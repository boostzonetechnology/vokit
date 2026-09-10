import shared_kernel.ids
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AuditEvent",
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
                ("actor_id", models.UUIDField(blank=True, null=True)),
                ("actor_role", models.CharField(blank=True, default="", max_length=64)),
                ("tenant_id", models.UUIDField(blank=True, null=True)),
                ("customer_id", models.UUIDField(blank=True, null=True)),
                ("action", models.CharField(max_length=64)),
                ("entity_type", models.CharField(max_length=64)),
                ("entity_id", models.CharField(blank=True, default="", max_length=64)),
                ("severity", models.CharField(max_length=16)),
                (
                    "correlation_id",
                    models.CharField(blank=True, default="", max_length=64),
                ),
                ("ip", models.CharField(blank=True, default="", max_length=64)),
                ("user_agent", models.CharField(blank=True, default="", max_length=255)),
                ("reason", models.CharField(blank=True, default="", max_length=255)),
                (
                    "before_summary",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "after_summary",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "audit_events"},
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(
                fields=["action", "created_at"], name="idx_audit_action_time"
            ),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(
                fields=["tenant_id", "created_at"], name="idx_audit_tenant_time"
            ),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(
                fields=["actor_id", "created_at"], name="idx_audit_actor_time"
            ),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(
                fields=["entity_type", "entity_id"], name="idx_audit_entity"
            ),
        ),
    ]
