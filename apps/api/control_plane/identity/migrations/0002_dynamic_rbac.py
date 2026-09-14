"""
Phase 0-3: Dynamic DB RBAC — ADR-007.

Creates:
  identity_permissions, identity_roles, identity_role_permissions

Updates:
  identity_memberships  — removes role CharField, adds role FK (role_id)
  identity_invitations  — removes role CharField, adds role FK (role_id)

Since fresh DB is acceptable (tests reseed via ensure_rbac_seeded), no data
migration is required. role FK is nullable so the migration runs against an
empty or seeded table without error.
"""

from __future__ import annotations

import django.db.models.deletion
import shared_kernel.ids
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("identity", "0001_phase2_identity"),
    ]

    operations = [
        # ------------------------------------------------------------------
        # 1. Permission catalog table
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="Permission",
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
                ("namespace", models.CharField(max_length=32)),
                ("code", models.CharField(max_length=64)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("is_sensitive", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "identity_permissions"},
        ),
        migrations.AddConstraint(
            model_name="permission",
            constraint=models.UniqueConstraint(
                fields=["namespace", "code"],
                name="identity_permission_namespace_code_uniq",
            ),
        ),
        # ------------------------------------------------------------------
        # 2. Roles table
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="Role",
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
                ("namespace", models.CharField(max_length=32)),
                ("slug", models.CharField(max_length=64, unique=True)),
                ("display_name", models.CharField(max_length=128)),
                ("is_system", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "identity_roles"},
        ),
        # ------------------------------------------------------------------
        # 3. Role-permission pivot
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="RolePermission",
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
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_permissions",
                        to="identity.role",
                    ),
                ),
                (
                    "permission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_permissions",
                        to="identity.permission",
                    ),
                ),
            ],
            options={"db_table": "identity_role_permissions"},
        ),
        migrations.AddConstraint(
            model_name="rolepermission",
            constraint=models.UniqueConstraint(
                fields=["role", "permission"],
                name="identity_rolepermission_role_permission_uniq",
            ),
        ),
        # ------------------------------------------------------------------
        # 4. Membership: remove old role CharField, add role FK
        # ------------------------------------------------------------------
        migrations.RemoveField(
            model_name="membership",
            name="role",
        ),
        migrations.AddField(
            model_name="membership",
            name="role",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="memberships",
                to="identity.role",
            ),
        ),
        # ------------------------------------------------------------------
        # 5. Invitation: remove old role CharField, add role FK
        # ------------------------------------------------------------------
        migrations.RemoveField(
            model_name="invitation",
            name="role",
        ),
        migrations.AddField(
            model_name="invitation",
            name="role",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="invitations",
                to="identity.role",
            ),
        ),
    ]
