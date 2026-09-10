import shared_kernel.ids
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NotificationTemplate",
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
                ("event_type", models.CharField(max_length=64)),
                ("channel", models.CharField(max_length=16)),
                ("subject", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("version", models.PositiveIntegerField(default=1)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "notification_templates"},
        ),
        migrations.AddConstraint(
            model_name="notificationtemplate",
            constraint=models.UniqueConstraint(
                fields=["event_type", "channel"],
                name="uniq_notification_template_channel",
            ),
        ),
        migrations.CreateModel(
            name="InAppNotification",
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
                ("user_id", models.UUIDField()),
                ("tenant_id", models.UUIDField(blank=True, null=True)),
                ("customer_id", models.UUIDField(blank=True, null=True)),
                ("event_type", models.CharField(max_length=64)),
                ("category", models.CharField(max_length=32)),
                ("title", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "in_app_notifications"},
        ),
        migrations.AddIndex(
            model_name="inappnotification",
            index=models.Index(
                fields=["user_id", "created_at"], name="idx_inapp_user_time"
            ),
        ),
        migrations.AddIndex(
            model_name="inappnotification",
            index=models.Index(
                fields=["tenant_id", "user_id"], name="idx_inapp_tenant_user"
            ),
        ),
        migrations.CreateModel(
            name="NotificationDelivery",
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
                ("user_id", models.UUIDField(blank=True, null=True)),
                ("recipient_email", models.CharField(max_length=254)),
                ("channel", models.CharField(max_length=16)),
                ("event_type", models.CharField(max_length=64)),
                ("status", models.CharField(max_length=16)),
                ("error", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "notification_deliveries"},
        ),
        migrations.AddIndex(
            model_name="notificationdelivery",
            index=models.Index(
                fields=["event_type", "created_at"], name="idx_ndel_event_time"
            ),
        ),
        migrations.AddIndex(
            model_name="notificationdelivery",
            index=models.Index(
                fields=["recipient_email", "created_at"], name="idx_ndel_email"
            ),
        ),
        migrations.CreateModel(
            name="NotificationPreference",
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
                ("scope", models.CharField(max_length=16)),
                ("user_id", models.UUIDField(blank=True, null=True)),
                ("tenant_id", models.UUIDField(blank=True, null=True)),
                ("customer_id", models.UUIDField(blank=True, null=True)),
                ("event_type", models.CharField(max_length=64)),
                ("email_enabled", models.BooleanField(default=True)),
                ("in_app_enabled", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "notification_preferences"},
        ),
        migrations.AddIndex(
            model_name="notificationpreference",
            index=models.Index(
                fields=["scope", "tenant_id"], name="idx_npref_scope_tenant"
            ),
        ),
        migrations.AddIndex(
            model_name="notificationpreference",
            index=models.Index(
                fields=["user_id", "event_type"], name="idx_npref_user_event"
            ),
        ),
    ]
