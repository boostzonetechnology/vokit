from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agents", "0001_phase9_agents"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentindex",
            name="status_locked",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="agentindex",
            name="status_actor",
            field=models.CharField(default="agency", max_length=16),
        ),
    ]
