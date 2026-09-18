from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0002_billingsettings_sandbox_webhook_secret_ref"),
    ]

    operations = [
        migrations.AddField(
            model_name="planversion",
            name="max_agents",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="planversion",
            name="max_phone_numbers",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="planversion",
            name="max_concurrency",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="planversion",
            name="recording_allowed",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="planversion",
            name="allowed_integrations",
            field=models.JSONField(default=list),
        ),
    ]
