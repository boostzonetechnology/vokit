from __future__ import annotations

import json
import uuid
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from control_plane.tenancy.infrastructure.container import backup_tenant, database_repo
from shared_kernel.errors import DomainError


class Command(BaseCommand):
    help = "Export one tenant data-plane snapshot. Never prints passwords."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--tenant-id", required=True)
        parser.add_argument("--out", required=True)

    def handle(self, *args, **options) -> None:
        tenant_id = uuid.UUID(str(options["tenant_id"]))
        try:
            snapshot = backup_tenant().execute(tenant_id)
        except DomainError as exc:
            if exc.code != "backup_use_logical_dump":
                raise CommandError(exc.message) from exc
            database = database_repo().get_for_tenant(tenant_id)
            if database is None:
                raise CommandError("Tenant database is not registered.") from exc
            plan = {
                "plane": "tenant",
                "mode": "logical_dump",
                "tenant_id": str(tenant_id),
                "database_name": database.name,
                "secret_ref": database.secret_ref,
                "command": [
                    "mysqldump",
                    "--single-transaction",
                    "--set-gtid-purged=OFF",
                    "--databases",
                    database.name,
                ],
            }
            Path(options["out"]).write_text(json.dumps(plan, indent=2), encoding="utf-8")
            self.stdout.write(
                f"Wrote logical dump plan for {tenant_id} using {database.secret_ref}."
            )
            return
        Path(options["out"]).write_text(
            json.dumps(snapshot.to_public_dict(), indent=2),
            encoding="utf-8",
        )
        self.stdout.write(f"Wrote tenant snapshot for {tenant_id}.")
