"""MFA method, challenge, and recovery code tables (SEC-013 / VKT-007)."""

from __future__ import annotations

import django.db.models.deletion
import shared_kernel.ids
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("identity", "0003_permission_is_custom"),
    ]

    operations = [
        migrations.CreateModel(
            name="MfaMethod",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=shared_kernel.ids.new_uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("method_type", models.CharField(max_length=16)),
                ("status", models.CharField(default="pending", max_length=16)),
                ("secret_ciphertext", models.CharField(blank=True, default="", max_length=1024)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("disabled_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mfa_methods",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "identity_mfa_methods"},
        ),
        migrations.CreateModel(
            name="MfaChallenge",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=shared_kernel.ids.new_uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("purpose", models.CharField(max_length=16)),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("code_hash", models.CharField(blank=True, default="", max_length=64)),
                ("expires_at", models.DateTimeField()),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("max_attempts", models.PositiveIntegerField(default=5)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mfa_challenges",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "method",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="challenges",
                        to="identity.mfamethod",
                    ),
                ),
            ],
            options={"db_table": "identity_mfa_challenges"},
        ),
        migrations.CreateModel(
            name="MfaRecoveryCode",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=shared_kernel.ids.new_uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("code_hash", models.CharField(max_length=64)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mfa_recovery_codes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "identity_mfa_recovery_codes"},
        ),
        migrations.AddIndex(
            model_name="mfamethod",
            index=models.Index(fields=["user", "status"], name="idx_mfa_method_user"),
        ),
        migrations.AddIndex(
            model_name="mfachallenge",
            index=models.Index(fields=["user", "purpose"], name="idx_mfa_chal_user"),
        ),
        migrations.AddIndex(
            model_name="mfarecoverycode",
            index=models.Index(fields=["user", "used_at"], name="idx_mfa_recovery_user"),
        ),
    ]
