"""
Management command: seed system roles and attach permission bundles.

Usage:
    python manage.py seed_system_roles

Run after sync_permissions (or call ensure_rbac_seeded which does both).
Idempotent — safe to run multiple times.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from control_plane.identity.infrastructure.rbac_seed import ensure_rbac_seeded


class Command(BaseCommand):
    help = "Seed system roles and attach permission bundles (idempotent)."

    def handle(self, *args, **options) -> None:
        ensure_rbac_seeded()
        self.stdout.write(self.style.SUCCESS("seed_system_roles: complete."))
