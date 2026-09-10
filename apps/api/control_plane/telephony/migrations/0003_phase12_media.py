from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("telephony", "0002_phase11_calls"),
    ]

    operations = [
        migrations.AddField(
            model_name="callindex",
            name="remote_e164",
            field=models.CharField(blank=True, default="", max_length=16),
        ),
        migrations.AddField(
            model_name="callindex",
            name="transfer_destination_id",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="callindex",
            name="voicemail_status",
            field=models.CharField(blank=True, default="", max_length=16),
        ),
        migrations.AddField(
            model_name="callindex",
            name="hunt_index",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name="TransferDestinationIndex",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField()),
                ("customer_id", models.UUIDField()),
                ("kind", models.CharField(max_length=16)),
                ("label", models.CharField(max_length=128)),
                ("status", models.CharField(default="active", max_length=16)),
                ("platform_disabled", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "transfer_destination_index"},
        ),
        migrations.AddIndex(
            model_name="transferdestinationindex",
            index=models.Index(
                fields=["tenant_id", "customer_id"], name="idx_xfer_idx_tenant"
            ),
        ),
    ]
