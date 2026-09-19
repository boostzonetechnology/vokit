# Generated manually for AG11-004 payout methods.

from django.db import migrations, models
import shared_kernel.ids


class Migration(migrations.Migration):
    dependencies = [
        ("commission", "0001_phase7_commission"),
    ]

    operations = [
        migrations.CreateModel(
            name="AgencyPayoutMethod",
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
                ("beneficiary_name", models.CharField(max_length=128)),
                ("account_identifier", models.CharField(max_length=128)),
                ("bank_name", models.CharField(max_length=128)),
                ("country", models.CharField(max_length=2)),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("label", models.CharField(max_length=64)),
                ("status", models.CharField(default="pending", max_length=16)),
                ("is_default", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "commission_payout_methods",
            },
        ),
        migrations.AddIndex(
            model_name="agencypayoutmethod",
            index=models.Index(
                fields=["tenant_id", "status"], name="idx_payout_method_tenant"
            ),
        ),
    ]
