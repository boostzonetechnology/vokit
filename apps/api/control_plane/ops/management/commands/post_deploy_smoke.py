from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from control_plane.ops.infrastructure.container import post_deploy_smoke
from shared_kernel.errors import DomainError


class Command(BaseCommand):
    help = "In-process post-deploy smoke: /health, /ready, /api/v1/health."

    def handle(self, *args, **options) -> None:
        try:
            payload = post_deploy_smoke().execute()
        except DomainError as exc:
            raise CommandError(exc.message) from exc
        self.stdout.write(json.dumps(payload, indent=2))
