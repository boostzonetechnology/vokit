from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from control_plane.tenancy.infrastructure.container import backup_control_plane


class Command(BaseCommand):
    help = "Export control-plane tenant registry metadata (secret refs only)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--out", required=True)

    def handle(self, *args, **options) -> None:
        document = backup_control_plane().execute()
        Path(options["out"]).write_text(json.dumps(document, indent=2), encoding="utf-8")
        count = len(document["tenants"])
        self.stdout.write(f"Wrote control-plane registry snapshot ({count} tenants).")
