"""Role and permission catalogs. Namespaces cannot be mixed (RBAC-005, RBAC-006)."""

from __future__ import annotations

from control_plane.identity.domain.types import PrincipalType
from shared_kernel.errors import DomainError

# Sensitive permissions stay explicit even when unused by a given role (SA18-003).
PLATFORM_PERMISSIONS = frozenset(
    {
        "users.invite",
        "users.disable",
        "tenants.view",
        "tenants.provision",
        "tenants.migrate",
        "tenants.route",
        "agencies.view",
        "agencies.create",
        "agencies.manage",
        "customers.view",
        "customers.create",
        "plans.manage",
        "billing.view",
        "kyc.review",
        "risk.review",
        "agents.review",
        "numbers.review",
        "calls.review",
        "transfers.review",
        "recordings.review",
        "integrations.review",
        "audit.view",
        "settings.manage",
        "notifications.manage",
        "payout.approve",
        "wallet.adjust",
        "commission.edit",
        "impersonation.use",
    }
)
AGENCY_PERMISSIONS = frozenset(
    {
        "team.invite",
        "team.disable",
        "customers.manage",
        "agents.manage",
        "numbers.manage",
        "transfers.manage",
        "calls.view",
        "recordings.view",
        "recordings.hold",
        "integrations.manage",
        "webhooks.manage",
        "notices.configure",
        "wallet.view",
        "payout.request",
    }
)
CUSTOMER_PERMISSIONS = frozenset(
    {
        "team.invite",
        "team.disable",
        "billing.pay",
        "agents.view",
        "calls.view",
        "recordings.view",
        "risk.verify",
        "knowledge.view",
        "integrations.view",
        "integrations.connect",
        "notices.configure",
    }
)

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "super_admin": PLATFORM_PERMISSIONS,
    "finance_admin": frozenset({"payout.approve", "wallet.adjust", "billing.view"}),
    "compliance_kyc": frozenset({"kyc.review", "risk.review", "recordings.review"}),
    "support_admin": frozenset(),
    "agency_owner": AGENCY_PERMISSIONS,
    "agency_admin": frozenset(
        {
            "team.invite",
            "team.disable",
            "customers.manage",
            "agents.manage",
            "numbers.manage",
            "transfers.manage",
            "calls.view",
            "recordings.view",
            "integrations.manage",
            "webhooks.manage",
            "notices.configure",
        }
    ),
    "agency_agent_builder": frozenset(
        {"agents.manage", "transfers.manage", "integrations.manage"}
    ),
    "agency_finance": frozenset({"wallet.view", "payout.request"}),
    "customer_owner": CUSTOMER_PERMISSIONS,
    "customer_admin": frozenset(
        {
            "team.invite",
            "team.disable",
            "billing.pay",
            "agents.view",
            "calls.view",
            "recordings.view",
            "risk.verify",
            "knowledge.view",
            "integrations.view",
            "integrations.connect",
            "notices.configure",
        }
    ),
    "customer_analyst": frozenset(
        {"agents.view", "calls.view", "recordings.view", "integrations.view"}
    ),
}

PLATFORM_ROLES = frozenset({"super_admin", "finance_admin", "compliance_kyc", "support_admin"})
AGENCY_ROLES = frozenset({"agency_owner", "agency_admin", "agency_agent_builder", "agency_finance"})
CUSTOMER_ROLES = frozenset({"customer_owner", "customer_admin", "customer_analyst"})


def namespace_for_role(role: str) -> PrincipalType:
    if role in PLATFORM_ROLES:
        return PrincipalType.PLATFORM
    if role in AGENCY_ROLES:
        return PrincipalType.AGENCY
    if role in CUSTOMER_ROLES:
        return PrincipalType.CUSTOMER
    raise DomainError("invalid_role", "Unknown role.")


def permissions_for_role(role: str) -> frozenset[str]:
    perms = ROLE_PERMISSIONS.get(role)
    if perms is None:
        raise DomainError("invalid_role", "Unknown role.")
    namespace = namespace_for_role(role)
    catalog = {
        PrincipalType.PLATFORM: PLATFORM_PERMISSIONS,
        PrincipalType.AGENCY: AGENCY_PERMISSIONS,
        PrincipalType.CUSTOMER: CUSTOMER_PERMISSIONS,
    }[namespace]
    if not perms.issubset(catalog):
        raise DomainError("invalid_role", "Role mixes permission namespaces.")
    return perms


def assert_role_matches_principal(role: str, principal_type: PrincipalType) -> None:
    if namespace_for_role(role) != principal_type:
        raise DomainError("invalid_role", "Role does not belong to this permission namespace.")
