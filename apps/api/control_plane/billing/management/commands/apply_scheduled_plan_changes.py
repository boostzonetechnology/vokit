from __future__ import annotations

from django.core.management.base import BaseCommand

from control_plane.billing.application.entitlements import apply_due_plan_change
from control_plane.billing.infrastructure.container import plan_versions, tenant_billing
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.tenancy.infrastructure.container import tenant_repo


class Command(BaseCommand):
    help = "Apply due scheduled plan downgrades."

    def handle(self, *args, **options) -> None:
        billing = tenant_billing()
        versions = plan_versions()
        now = SystemClock().now()
        applied = 0
        for tenant in tenant_repo().list():
            for subscription in billing.list_active_subscriptions(tenant.id):
                updated = apply_due_plan_change(billing, versions, subscription, now)
                if updated.plan_version_id != subscription.plan_version_id:
                    applied += 1
        self.stdout.write(f"applied={applied}")
