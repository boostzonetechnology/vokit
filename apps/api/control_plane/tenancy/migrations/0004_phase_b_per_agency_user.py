import django.db.models.deletion
import shared_kernel.ids
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenancy", "0003_phase_sa2_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenantdatabase",
            name="db_username",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.CreateModel(
            name="TenantDbCredential",
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
                ("ciphertext", models.CharField(max_length=1024)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "database",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="credential",
                        to="tenancy.tenantdatabase",
                    ),
                ),
            ],
            options={
                "db_table": "tenant_db_credentials",
            },
        ),
    ]
