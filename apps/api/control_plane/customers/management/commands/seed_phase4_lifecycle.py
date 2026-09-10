from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from control_plane.customers.application.create_customer import CreateCustomerCommand
from control_plane.customers.infrastructure.container import (
    create_customer,
    customer_index,
)
from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.demo import (
    DEMO_AGENCY_B_TENANT_ID,
    DEMO_AGENCY_TENANT_ID,
    DEMO_CUSTOMER_B_EMAIL,
    DEMO_CUSTOMER_B_ID,
    DEMO_CUSTOMER_EMAIL,
    DEMO_CUSTOMER_ID,
    DEMO_PLATFORM_EMAIL,
)
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.container import memberships
from control_plane.identity.models import User
from control_plane.tenancy.application.create_agency import CreateAgencyCommand
from control_plane.tenancy.domain.lifecycle import AgencyCapabilities
from control_plane.tenancy.infrastructure.container import create_agency
from shared_kernel.ids import new_uuid7


class Command(BaseCommand):
    help = "Activate demo agencies and create isolated demo customers."

    def handle(self, *args, **options) -> None:
        user = User.objects.filter(email=DEMO_PLATFORM_EMAIL).first()
        if user is None:
            raise CommandError("Run seed_phase2_demo first.")
        actor = memberships().get_for_user(user.id)
        if actor is None:
            actor = MembershipRecord(
                id=new_uuid7(),
                user_id=user.id,
                principal_type=PrincipalType.PLATFORM,
                role="super_admin",
                tenant_id=None,
                customer_id=None,
                status=MembershipStatus.ACTIVE,
            )
        name_a = getattr(settings, "TENANT_DB_NAME_A", "vokit_tenant_a")
        name_b = getattr(settings, "TENANT_DB_NAME_B", "vokit_tenant_b")
        specs = (
            (DEMO_AGENCY_TENANT_ID, "Demo Agency A", name_a, "agency-a@example.test"),
            (DEMO_AGENCY_B_TENANT_ID, "Demo Agency B", name_b, "agency-b-owner@example.test"),
        )
        for tenant_id, name, db_name, owner in specs:
            created = create_agency().execute(
                CreateAgencyCommand(
                    display_name=name,
                    legal_name=name,
                    owner_email=owner,
                    actor=actor,
                    commission_rate_bps=1500,
                    tenant_id=tenant_id,
                    database_name=db_name,
                    capabilities=AgencyCapabilities(),
                )
            )
            status = created.tenant.agency_status.value
            self.stdout.write(f"Agency {created.tenant.id} status={status}")
        customers = (
            (DEMO_AGENCY_TENANT_ID, DEMO_CUSTOMER_ID, "Demo Customer A", DEMO_CUSTOMER_EMAIL),
            (DEMO_AGENCY_B_TENANT_ID, DEMO_CUSTOMER_B_ID, "Demo Customer B", DEMO_CUSTOMER_B_EMAIL),
        )
        for tenant_id, customer_id, name, email in customers:
            if customer_index().get(customer_id) is not None:
                self.stdout.write(f"Customer {customer_id} already indexed")
                continue
            created = create_customer().execute(
                CreateCustomerCommand(
                    display_name=name,
                    agency_tenant_id=tenant_id,
                    actor=actor,
                    privileged=True,
                    owner_email=email,
                    customer_id=customer_id,
                )
            )
            self.stdout.write(f"Customer {created.customer.customer_id}")
