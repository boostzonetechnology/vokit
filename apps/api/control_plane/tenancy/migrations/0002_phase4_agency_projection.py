from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenancy", "0001_phase3_tenancy"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="agency_status",
            field=models.CharField(default="pending", max_length=32),
        ),
        migrations.AddField(
            model_name="tenant",
            name="legal_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="tenant",
            name="currency",
            field=models.CharField(default="USD", max_length=3),
        ),
        migrations.AddField(
            model_name="tenant",
            name="commission_rate_bps",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="tenant",
            name="rate_effective_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tenant",
            name="can_create_customers",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="tenant",
            name="can_create_agents",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="tenant",
            name="can_purchase_numbers",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="tenant",
            name="can_request_payouts",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="tenant",
            name="existing_customer_services",
            field=models.BooleanField(default=True),
        ),
    ]
