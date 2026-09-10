from __future__ import annotations

from django.core.management.base import BaseCommand

from control_plane.integrations.infrastructure.container import integration_control


class Command(BaseCommand):
    help = "Retry failed outbound webhook deliveries with bounded backoff."

    def handle(self, *args, **options) -> None:
        retried = integration_control().retry_pending()
        self.stdout.write(f"retried={retried}")
