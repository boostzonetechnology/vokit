from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agents", "0002_agent_index_status_lock"),
    ]

    operations = [
        migrations.AlterField(
            model_name="globalknowledgesource",
            name="status",
            field=models.CharField(default="queued", max_length=16),
        ),
        migrations.AddField(
            model_name="globalknowledgesource",
            name="kind",
            field=models.CharField(default="text", max_length=16),
        ),
        migrations.AddField(
            model_name="globalknowledgesource",
            name="object_ref",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="globalknowledgesource",
            name="checksum",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
    ]
