from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="IntegrationConnectionIndex",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField()),
                ("customer_id", models.UUIDField()),
                ("provider", models.CharField(max_length=32)),
                ("status", models.CharField(max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "integration_connection_index"},
        ),
        migrations.CreateModel(
            name="WebhookEndpointIndex",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField()),
                ("customer_id", models.UUIDField()),
                ("status", models.CharField(max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "webhook_endpoint_index"},
        ),
        migrations.AddIndex(
            model_name="integrationconnectionindex",
            index=models.Index(
                fields=["tenant_id", "customer_id"], name="idx_int_idx_customer"
            ),
        ),
        migrations.AddIndex(
            model_name="webhookendpointindex",
            index=models.Index(
                fields=["tenant_id", "customer_id"], name="idx_wh_idx_customer"
            ),
        ),
    ]
