from __future__ import annotations

from config.celery import app
from control_plane.commission.infrastructure.container import (
    reconcile_finance,
    release_holds,
)


@app.task(name="commission.release_holds")
def release_holds_task() -> int:
    return release_holds().execute()


@app.task(name="commission.reconcile_finance")
def reconcile_finance_task() -> dict[str, object]:
    report = reconcile_finance().execute()
    return {
        "invoices_paid": report.invoices_paid,
        "commissions_missing": report.commissions_missing,
        "commissions_repaired": report.commissions_repaired,
        "payouts_unbalanced": report.payouts_unbalanced,
        "mismatches": list(report.mismatches),
    }
