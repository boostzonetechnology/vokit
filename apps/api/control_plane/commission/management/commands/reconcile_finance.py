from __future__ import annotations

from django.core.management.base import BaseCommand

from control_plane.commission.infrastructure.container import reconcile_finance


class Command(BaseCommand):
    help = "Reconcile paid invoices, commissions, and payouts."

    def handle(self, *args, **options) -> None:
        report = reconcile_finance().execute()
        self.stdout.write(
            f"invoices_paid={report.invoices_paid} "
            f"missing={report.commissions_missing} "
            f"repaired={report.commissions_repaired} "
            f"unbalanced={report.payouts_unbalanced}"
        )
        for item in report.mismatches:
            self.stdout.write(item)
