"""Persist platform terms acceptance on invitation accept (VKT-024 / SRS §6.1)."""

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("identity", "0004_mfa_methods"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="platform_terms_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="platform_terms_version",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
    ]
