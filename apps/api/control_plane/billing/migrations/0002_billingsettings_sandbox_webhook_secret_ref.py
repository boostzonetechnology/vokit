from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0001_phase6_billing"),
    ]

    operations = [
        migrations.AddField(
            model_name="billingsettings",
            name="sandbox_webhook_secret_ref",
            field=models.CharField(default="SANDBOX_WEBHOOK_SECRET", max_length=128),
        ),
    ]
