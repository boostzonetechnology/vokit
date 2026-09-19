from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("customers", "0001_phase4_customers"),
    ]

    operations = [
        migrations.AddField(
            model_name="customerindex",
            name="plan_id",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="customerindex",
            name="remaining_minutes",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="customerindex",
            name="payment_due",
            field=models.BooleanField(default=False),
        ),
    ]
