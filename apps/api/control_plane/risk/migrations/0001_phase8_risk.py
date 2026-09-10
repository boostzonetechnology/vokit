import django.db.models.deletion
import shared_kernel.ids
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RiskCase",
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
                ("tenant_id", models.UUIDField()),
                ("customer_id", models.UUIDField(unique=True)),
                ("status", models.CharField(default="normal", max_length=32)),
                ("last_invoice_id", models.UUIDField(blank=True, null=True)),
                ("last_payment_id", models.UUIDField(blank=True, null=True)),
                ("last_event_id", models.CharField(blank=True, default="", max_length=128)),
                ("note", models.CharField(blank=True, default="", max_length=255)),
                ("permanently_banned", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "risk_cases",
            },
        ),
        migrations.CreateModel(
            name="RiskEvent",
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
                ("processor", models.CharField(max_length=32)),
                ("event_id", models.CharField(max_length=128)),
                ("customer_id", models.UUIDField(blank=True, null=True)),
                ("kind", models.CharField(max_length=32)),
                ("status", models.CharField(default="received", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "risk_events",
                "unique_together": {("processor", "event_id")},
            },
        ),
        migrations.CreateModel(
            name="VerificationSubmission",
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
                ("status", models.CharField(default="submitted", max_length=32)),
                ("id_object_ref", models.CharField(max_length=128)),
                ("id_checksum", models.CharField(max_length=128)),
                ("card_object_ref", models.CharField(max_length=128)),
                ("card_checksum", models.CharField(max_length=128)),
                ("card_last4", models.CharField(max_length=4)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="verifications",
                        to="risk.riskcase",
                    ),
                ),
            ],
            options={
                "db_table": "risk_verifications",
            },
        ),
        migrations.AddIndex(
            model_name="riskcase",
            index=models.Index(fields=["tenant_id", "status"], name="idx_risk_tenant_status"),
        ),
    ]
