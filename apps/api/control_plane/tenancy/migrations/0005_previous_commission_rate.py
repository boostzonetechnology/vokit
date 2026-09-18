from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenancy", "0004_phase_b_per_agency_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="previous_commission_rate_bps",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
