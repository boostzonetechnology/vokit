from __future__ import annotations

import uuid

from django.core.management.base import BaseCommand, CommandError

from control_plane.tenancy.infrastructure.container import migration_batch, tenant_repo
from tenant.schema import CURRENT_VERSION


class Command(BaseCommand):
    help = "Apply tenant schema migrations with optional canary IDs."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--canary", action="append", default=[])
        parser.add_argument("--target", default=CURRENT_VERSION)
        parser.add_argument(
            "--canary-only",
            action="store_true",
            help="Migrate canary tenants and stop before the remaining batch.",
        )

    def handle(self, *args, **options) -> None:
        tenants = [row.id for row in tenant_repo().list()]
        if not tenants:
            raise CommandError("No tenants registered.")
        canary_ids = [uuid.UUID(item) for item in options["canary"]]
        if options["canary_only"] and not canary_ids:
            raise CommandError("--canary-only requires --canary.")
        jobs = migration_batch().execute(
            tenants,
            canary_ids=canary_ids,
            target_version=options["target"],
            canary_only=bool(options["canary_only"]),
        )
        for job in jobs:
            self.stdout.write(f"{job.tenant_id} {job.status.value} canary={job.canary}")
