import django.db.models.deletion
import shared_kernel.ids
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PhoneNumber",
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
                ("e164", models.CharField(max_length=16, unique=True)),
                ("country", models.CharField(default="US", max_length=8)),
                ("area", models.CharField(blank=True, default="", max_length=16)),
                ("capabilities", models.CharField(default="voice", max_length=64)),
                ("provider", models.CharField(default="platform", max_length=32)),
                ("provider_ref", models.CharField(blank=True, default="", max_length=128)),
                ("status", models.CharField(default="available", max_length=32)),
                ("monthly_cost_minor", models.BigIntegerField(default=0)),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("assigned_tenant_id", models.UUIDField(blank=True, null=True)),
                ("assigned_customer_id", models.UUIDField(blank=True, null=True)),
                ("assigned_agent_id", models.UUIDField(blank=True, null=True)),
                ("reservation_id", models.UUIDField(blank=True, null=True)),
                ("reserved_until", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "phone_numbers"},
        ),
        migrations.CreateModel(
            name="PhoneNumberReservation",
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
                ("customer_id", models.UUIDField()),
                ("agent_id", models.UUIDField()),
                ("status", models.CharField(default="active", max_length=32)),
                ("expires_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "number",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservations",
                        to="telephony.phonenumber",
                    ),
                ),
            ],
            options={"db_table": "phone_number_reservations"},
        ),
        migrations.AddIndex(
            model_name="phonenumber",
            index=models.Index(
                fields=["status", "country"], name="idx_phone_status_country"
            ),
        ),
        migrations.AddIndex(
            model_name="phonenumberreservation",
            index=models.Index(
                fields=["number", "status"], name="idx_reserve_number_status"
            ),
        ),
        migrations.AddIndex(
            model_name="phonenumberreservation",
            index=models.Index(
                fields=["expires_at", "status"], name="idx_reserve_expiry"
            ),
        ),
    ]
