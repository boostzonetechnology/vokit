from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.demo import (
    DEMO_AGENCY_B_EMAIL,
    DEMO_AGENCY_B_TENANT_ID,
    DEMO_AGENCY_TENANT_ID,
    DEMO_PASSWORD,
)
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from control_plane.tenancy.application.provision_tenant import ProvisionTenantCommand
from control_plane.tenancy.infrastructure.container import provisioner
from shared_kernel.ids import new_uuid7


class Command(BaseCommand):
    help = "Register and provision demo Agency A/B tenant databases."

    def handle(self, *args, **options) -> None:
        host = getattr(settings, "TENANT_DB_HOST", "127.0.0.1")
        port = int(getattr(settings, "TENANT_DB_PORT", 3306))
        tls = bool(getattr(settings, "TENANT_TLS_REQUIRED", False))
        name_a = getattr(settings, "TENANT_DB_NAME_A", "vokit_tenant_a")
        name_b = getattr(settings, "TENANT_DB_NAME_B", "vokit_tenant_b")
        specs = (
            (DEMO_AGENCY_TENANT_ID, "Demo Agency A", name_a),
            (DEMO_AGENCY_B_TENANT_ID, "Demo Agency B", name_b),
        )
        for tenant_id, name, database_name in specs:
            tenant = provisioner().execute(
                ProvisionTenantCommand(
                    display_name=name,
                    host=host,
                    port=port,
                    name=database_name,
                    db_username=f"demo_{tenant_id.hex[:16]}",
                    db_password="DemoTenantPass12!",
                    tls_required=tls,
                    tenant_id=tenant_id,
                )
            )
            status = tenant.status.value
            self.stdout.write(self.style.SUCCESS(f"Tenant {tenant.id} status={status}"))
        user = User.objects.filter(email=DEMO_AGENCY_B_EMAIL).first()
        if user is None:
            user = User.objects.create_user(email=DEMO_AGENCY_B_EMAIL, password=DEMO_PASSWORD)
            DjangoMembershipRepository().create(
                MembershipRecord(
                    id=new_uuid7(),
                    user_id=user.id,
                    principal_type=PrincipalType.AGENCY,
                    role="agency_owner",
                    tenant_id=DEMO_AGENCY_B_TENANT_ID,
                    customer_id=None,
                    status=MembershipStatus.ACTIVE,
                )
            )
            self.stdout.write(self.style.SUCCESS(f"Created {DEMO_AGENCY_B_EMAIL}"))
