import shared_kernel.ids
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("telephony", "0001_phase10_numbers"),
    ]

    operations = [
        migrations.CreateModel(
            name="CallIndex",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField()),
                ("customer_id", models.UUIDField()),
                ("agent_id", models.UUIDField()),
                ("edge_call_id", models.CharField(max_length=128, unique=True)),
                ("e164", models.CharField(max_length=16)),
                ("direction", models.CharField(max_length=16)),
                ("status", models.CharField(max_length=32)),
                ("transfer_status", models.CharField(default="idle", max_length=32)),
                ("billed_minutes", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "call_index"},
        ),
        migrations.CreateModel(
            name="TrainingSessionIndex",
            fields=[
                ("session_id", models.UUIDField(primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField()),
                ("customer_id", models.UUIDField()),
                ("agent_id", models.UUIDField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "training_session_index"},
        ),
        migrations.CreateModel(
            name="TrainingProposal",
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
                ("session_id", models.UUIDField()),
                ("kind", models.CharField(max_length=32)),
                ("name", models.CharField(max_length=128)),
                ("scope", models.CharField(blank=True, default="", max_length=32)),
                ("status", models.CharField(default="proposed", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "training_proposals"},
        ),
        migrations.AddIndex(
            model_name="callindex",
            index=models.Index(
                fields=["tenant_id", "customer_id"], name="idx_call_idx_tenant"
            ),
        ),
    ]
