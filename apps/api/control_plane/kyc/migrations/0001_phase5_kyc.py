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
            name="KycSettings",
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
                ("provider_slug", models.CharField(default="external", max_length=32)),
                ("api_key_ref", models.CharField(default="KYC_API_KEY", max_length=128)),
                (
                    "webhook_secret_ref",
                    models.CharField(default="KYC_WEBHOOK_SECRET", max_length=128),
                ),
                (
                    "hosted_base_url",
                    models.CharField(
                        default="https://kyc.example.test", max_length=255
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "kyc_settings"},
        ),
        migrations.CreateModel(
            name="KycCase",
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
                ("status", models.CharField(default="not_started", max_length=32)),
                ("provider_slug", models.CharField(default="external", max_length=32)),
                ("session_id", models.CharField(blank=True, default="", max_length=128)),
                ("inquiry_id", models.CharField(blank=True, default="", max_length=128)),
                (
                    "last_event_id",
                    models.CharField(blank=True, default="", max_length=128),
                ),
                ("reason_code", models.CharField(blank=True, default="", max_length=64)),
                (
                    "external_note",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "internal_note",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("frozen", models.BooleanField(default=False)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="kyc_case",
                        to="tenancy.tenant",
                    ),
                ),
            ],
            options={"db_table": "kyc_cases"},
        ),
        migrations.CreateModel(
            name="KycProviderEvent",
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
                ("event_id", models.CharField(max_length=128, unique=True)),
                ("mapped_status", models.CharField(blank=True, default="", max_length=32)),
                ("reason_code", models.CharField(blank=True, default="", max_length=64)),
                ("status", models.CharField(default="received", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "case",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="events",
                        to="kyc.kyccase",
                    ),
                ),
            ],
            options={"db_table": "kyc_provider_events"},
        ),
    ]
