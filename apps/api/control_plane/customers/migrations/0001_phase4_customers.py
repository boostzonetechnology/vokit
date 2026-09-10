import django.db.models.deletion
import shared_kernel.ids
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("tenancy", "0002_phase4_agency_projection"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerIndex",
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
                ("display_name", models.CharField(max_length=255)),
                ("status", models.CharField(default="active", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="customer_index_rows",
                        to="tenancy.tenant",
                    ),
                ),
            ],
            options={"db_table": "customer_index"},
        ),
        migrations.CreateModel(
            name="BannedCustomerKey",
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
                ("kind", models.CharField(max_length=32)),
                ("key_hash", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "banned_customer_index"},
        ),
        migrations.AddConstraint(
            model_name="bannedcustomerkey",
            constraint=models.UniqueConstraint(
                fields=("kind", "key_hash"),
                name="customers_ban_key_unique",
            ),
        ),
    ]
