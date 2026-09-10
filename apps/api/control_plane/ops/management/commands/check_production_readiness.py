from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from control_plane.ops.domain.types import GateMode, GateVerdict
from control_plane.ops.infrastructure.container import production_readiness


class Command(BaseCommand):
    help = "Evaluate production go/no-go. Live items need dated attestations."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--lab",
            action="store_true",
            help="Score lab/CI evidence only (LAB_READY), skip live attestations.",
        )
        parser.add_argument("--out", default="")

    def handle(self, *args, **options) -> None:
        mode = GateMode.LAB if options["lab"] else GateMode.PRODUCTION
        report = production_readiness().execute(mode)
        payload = report.to_public_dict()
        text = json.dumps(payload, indent=2)
        if options["out"]:
            from pathlib import Path

            Path(options["out"]).write_text(text, encoding="utf-8")
        self.stdout.write(text)
        if report.verdict is GateVerdict.NO_GO:
            raise CommandError(f"Readiness verdict is {report.verdict.value}.")
        self.stdout.write(f"Verdict: {report.verdict.value}")
