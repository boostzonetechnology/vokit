# Generated manually for ADR-007 is_custom flag

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("identity", "0002_dynamic_rbac"),
    ]

    operations = [
        migrations.AddField(
            model_name="permission",
            name="is_custom",
            field=models.BooleanField(default=False),
        ),
    ]
