from __future__ import annotations

from django.core.management.base import BaseCommand

from control_plane.commission.infrastructure.container import release_holds


class Command(BaseCommand):
    help = "Insert hold-released ledger events for matured commissions."

    def handle(self, *args, **options) -> None:
        count = release_holds().execute()
        self.stdout.write(f"released={count}")
