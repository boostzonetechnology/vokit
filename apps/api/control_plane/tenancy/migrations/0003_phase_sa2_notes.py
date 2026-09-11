from django.db import migrations, models
import django.db.models.deletion
import shared_kernel.ids


class Migration(migrations.Migration):
    dependencies = [
        ("tenancy", "0002_phase4_agency_projection"),
    ]

    operations = [
        migrations.CreateModel(
            name="AgencyNote",
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
                ("body", models.TextField(max_length=2000)),
                ("risk_flag", models.BooleanField(default=False)),
                ("created_by_id", models.UUIDField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notes",
                        to="tenancy.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "agency_notes",
            },
        ),
        migrations.AddIndex(
            model_name="agencynote",
            index=models.Index(
                fields=["tenant", "-created_at"], name="idx_agency_notes_tenant"
            ),
        ),
    ]
