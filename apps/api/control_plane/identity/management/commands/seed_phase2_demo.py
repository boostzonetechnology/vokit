from __future__ import annotations

from django.core.management.base import BaseCommand

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.demo import (
    DEMO_AGENCY_EMAIL,
    DEMO_AGENCY_TENANT_ID,
    DEMO_CUSTOMER_EMAIL,
    DEMO_CUSTOMER_ID,
    DEMO_PASSWORD,
    DEMO_PLATFORM_EMAIL,
)
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import User
from shared_kernel.ids import new_uuid7


class Command(BaseCommand):
    help = "Seed Phase 2 demo platform, agency, and customer users."

    def handle(self, *args, **options) -> None:
        repo = DjangoMembershipRepository()
        specs = (
            (DEMO_PLATFORM_EMAIL, PrincipalType.PLATFORM, "super_admin", None, None),
            (DEMO_AGENCY_EMAIL, PrincipalType.AGENCY, "agency_owner", DEMO_AGENCY_TENANT_ID, None),
            (
                DEMO_CUSTOMER_EMAIL,
                PrincipalType.CUSTOMER,
                "customer_owner",
                DEMO_AGENCY_TENANT_ID,
                DEMO_CUSTOMER_ID,
            ),
        )
        for email, principal, role, tenant_id, customer_id in specs:
            user = User.objects.filter(email=email).first()
            if user is None:
                user = User.objects.create_user(email=email, password=DEMO_PASSWORD)
                self.stdout.write(self.style.SUCCESS(f"Created {email}"))
            else:
                self.stdout.write(self.style.WARNING(f"User {email} already exists."))
            if repo.get_for_user(user.id) is None:
                repo.create(
                    MembershipRecord(
                        id=new_uuid7(),
                        user_id=user.id,
                        principal_type=principal,
                        role=role,
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        status=MembershipStatus.ACTIVE,
                    )
                )
        self.stdout.write(f"Demo password: {DEMO_PASSWORD}")
        self.stdout.write(f"Demo agency tenant_id: {DEMO_AGENCY_TENANT_ID}")
        self.stdout.write(f"Demo customer_id: {DEMO_CUSTOMER_ID}")
