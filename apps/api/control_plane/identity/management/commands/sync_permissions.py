"""
Management command: sync the permission catalog into DB (additive).

Usage:
    python manage.py sync_permissions

Idempotent. Adds any missing Permission rows and updates description /
is_sensitive in place. Never deletes existing permissions.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from control_plane.identity.domain.permission_catalog import PERMISSION_CATALOG
from control_plane.identity.models import Permission
from shared_kernel.ids import new_uuid7


class Command(BaseCommand):
    help = "Sync the permission catalog into DB (additive, idempotent)."

    def handle(self, *args, **options) -> None:
        added = 0
        updated = 0
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
            if created:
                added += 1
            else:
                fields_changed = []
                if obj.description != spec.description:
                    obj.description = spec.description
                    fields_changed.append("description")
                if obj.is_sensitive != spec.is_sensitive:
                    obj.is_sensitive = spec.is_sensitive
                    fields_changed.append("is_sensitive")
                if fields_changed:
                    obj.save(update_fields=fields_changed)
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"sync_permissions: {added} added, {updated} updated, "
                f"{len(PERMISSION_CATALOG) - added - updated} unchanged."
            )
        )
