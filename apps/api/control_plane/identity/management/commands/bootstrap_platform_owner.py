from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.infrastructure.rbac_seed import ensure_rbac_seeded
from control_plane.identity.infrastructure.repositories import DjangoMembershipRepository
from control_plane.identity.models import Role, User
from shared_kernel.ids import new_uuid7


class Command(BaseCommand):
    help = "Create the first platform Super Admin. Idempotent on email."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)

    def handle(self, *args, **options) -> None:
        email = str(options["email"]).strip().lower()
        password = str(options["password"])
        if len(password) < 12:
            raise CommandError("Password must be at least 12 characters.")

        # Ensure RBAC tables are seeded before looking up roles.
        ensure_rbac_seeded()

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"User {email} already exists."))
            return

        role_row = Role.objects.filter(slug="super_admin").first()
        if role_row is None:
            raise CommandError("super_admin role not found — run seed_system_roles first.")

        user = User.objects.create_user(email=email, password=password)
        DjangoMembershipRepository().create(
            MembershipRecord(
                id=new_uuid7(),
                user_id=user.id,
                principal_type=PrincipalType.PLATFORM,
                role="super_admin",
                role_id=role_row.id,
                tenant_id=None,
                customer_id=None,
                status=MembershipStatus.ACTIVE,
            )
        )
        self.stdout.write(self.style.SUCCESS(f"Created platform owner {email}"))
