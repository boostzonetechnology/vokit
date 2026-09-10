from __future__ import annotations

import json
import uuid
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from control_plane.tenancy.application.backup import snapshot_from_dict
from control_plane.tenancy.infrastructure.container import restore_tenant
from shared_kernel.errors import DomainError


class Command(BaseCommand):
    help = "Restore one tenant from a snapshot. Will not open another tenant DB."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--tenant-id", required=True)
        parser.add_argument("--snapshot", required=True)

    def handle(self, *args, **options) -> None:
        tenant_id = uuid.UUID(str(options["tenant_id"]))
        raw = json.loads(Path(options["snapshot"]).read_text(encoding="utf-8"))
        if raw.get("mode") == "logical_dump":
            raise CommandError(
                "Logical dump plans must be applied with mysql using the secret ref, "
                "not this in-process restore."
            )
        try:
            snapshot = snapshot_from_dict(raw)
            restore_tenant().execute(tenant_id, snapshot)
        except DomainError as exc:
            raise CommandError(exc.message) from exc
        self.stdout.write(f"Restored tenant {tenant_id} only.")
