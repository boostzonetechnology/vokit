from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("commission", "0002_agency_payout_methods"),
    ]

    operations = [
        migrations.AddField(
            model_name="payoutproof",
            name="agency_visible",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="payoutproof",
            name="agency_visible_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="payoutproof",
            name="agency_visible_by",
            field=models.UUIDField(blank=True, null=True),
        ),
    ]
