"""
Idempotent RBAC seed helper.

ensure_rbac_seeded() is the single entry point called by:
  - conftest.py autouse fixture (_seed_rbac)
  - bootstrap_platform_owner management command
  - seed_phase2_demo management command
  - sync_permissions / seed_system_roles management commands

Behaviour:
  1. Sync all PermissionSpec entries from permission_catalog — additive only
     (existing rows are never deleted; is_sensitive / description are updated
     if changed).
  2. Create or update all system Role rows.
  3. For each role, attach any missing permissions from its bundle
     (additive; no existing pivot rows are removed).
  4. super_admin gets zero pivot rows (bypass logic lives in AuthContext).
"""

from __future__ import annotations

from control_plane.identity.domain.permission_catalog import PERMISSION_CATALOG, ROLE_SEED_BUNDLES
from control_plane.identity.models import Permission, Role, RolePermission
from shared_kernel.ids import new_uuid7


def ensure_rbac_seeded() -> None:
    """Idempotently sync the permission catalog and system roles into the DB."""
    _sync_permissions()
    _seed_roles()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sync_permissions() -> None:
    """Insert any missing Permission rows; update description / is_sensitive."""
    for spec in PERMISSION_CATALOG:
        obj, created = Permission.objects.get_or_create(
            namespace=spec.namespace,
            code=spec.code,
            defaults={
                "id": new_uuid7(),
                "description": spec.description,
                "is_sensitive": spec.is_sensitive,
            },
        )
        if not created:
            # Keep description and sensitivity flag in sync with catalog.
            updated = False
            if obj.description != spec.description:
                obj.description = spec.description
                updated = True
            if obj.is_sensitive != spec.is_sensitive:
                obj.is_sensitive = spec.is_sensitive
                updated = True
            if updated:
                obj.save(update_fields=["description", "is_sensitive"])


def _seed_roles() -> None:
    """Create / update system Role rows and attach missing permission pivots."""
    for slug, config in ROLE_SEED_BUNDLES.items():
        namespace: str = config["namespace"]
        display_name: str = config["display_name"]
        permission_codes: frozenset[str] = config["permissions"]

        role, _ = Role.objects.get_or_create(
            slug=slug,
            defaults={
                "id": new_uuid7(),
                "namespace": namespace,
                "display_name": display_name,
                "is_system": True,
            },
        )

        if not permission_codes:
            # super_admin and support_admin — no pivot rows.
            continue

        # Build a map: code → Permission pk for this namespace.
        perm_map: dict[str, Permission] = {
            p.code: p
            for p in Permission.objects.filter(namespace=namespace, code__in=permission_codes)
        }

        # Fetch already-linked permission IDs for this role.
        existing_perm_ids: set = set(
            RolePermission.objects.filter(role=role).values_list("permission_id", flat=True)
        )

        # Add missing pivots.
        to_create = [
            RolePermission(id=new_uuid7(), role=role, permission=perm)
            for code, perm in perm_map.items()
            if perm.id not in existing_perm_ids
        ]
        if to_create:
            RolePermission.objects.bulk_create(to_create, ignore_conflicts=True)
