import shared_kernel.ids
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PlatformSetting",
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
                ("key", models.CharField(max_length=64, unique=True)),
                ("value", models.JSONField()),
                ("secret", models.BooleanField(default=False)),
                ("updated_by_id", models.UUIDField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "platform_settings"},
        ),
        migrations.CreateModel(
            name="AgencyFeatureFlag",
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
                ("flag", models.CharField(max_length=32)),
                ("enabled", models.BooleanField(default=True)),
                ("updated_by_id", models.UUIDField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "agency_feature_flags"},
        ),
        migrations.AddConstraint(
            model_name="agencyfeatureflag",
            constraint=models.UniqueConstraint(
                fields=["tenant_id", "flag"], name="uniq_agency_flag"
            ),
        ),
    ]
