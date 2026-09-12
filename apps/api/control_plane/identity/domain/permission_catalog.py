"""
Permission catalog — single source of truth for sync.

All permission codes follow {module}.{action} with singular module names.
Actions: view, create, update, delete, hold, request, approve, adjust, pay,
         verify, review, connect, provision, migrate, route, sync, use.

Namespaces: platform | agency | customer
Sensitive permissions are flagged is_sensitive=True and are platform-only
unless explicitly noted (recording.hold is agency-sensitive).

ADR-007.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PermissionSpec:
    namespace: str
    code: str
    description: str = ""
    is_sensitive: bool = False


# ---------------------------------------------------------------------------
# Platform namespace
# ---------------------------------------------------------------------------

_PLATFORM: list[PermissionSpec] = [
    # Users (platform team)
    PermissionSpec("platform", "user.view", "List/view platform users"),
    PermissionSpec("platform", "user.create", "Invite a new platform user"),
    PermissionSpec("platform", "user.delete", "Disable a platform user"),
    # Tenancy
    PermissionSpec("platform", "tenant.view", "View tenant registry entries"),
    PermissionSpec("platform", "tenant.provision", "Provision a new tenant database"),
    PermissionSpec("platform", "tenant.migrate", "Run tenant schema migrations"),
    PermissionSpec("platform", "tenant.route", "Administer tenant DB routing config"),
    # Agencies
    PermissionSpec("platform", "agency.view", "List/view agencies"),
    PermissionSpec("platform", "agency.create", "Create a new agency"),
    PermissionSpec("platform", "agency.update", "Update agency details"),
    PermissionSpec("platform", "agency.delete", "Delete/suspend an agency"),
    # Customers (platform-level)
    PermissionSpec("platform", "customer.view", "View customers across agencies"),
    PermissionSpec("platform", "customer.create", "Create customers (platform)"),
    PermissionSpec("platform", "customer.update", "Update customers (platform)"),
    # Plans
    PermissionSpec("platform", "plan.view", "View subscription plans"),
    PermissionSpec("platform", "plan.create", "Create a subscription plan"),
    PermissionSpec("platform", "plan.update", "Update a subscription plan"),
    PermissionSpec("platform", "plan.delete", "Delete a subscription plan"),
    # Billing
    PermissionSpec("platform", "billing.view", "View billing records"),
    # KYC (sensitive)
    PermissionSpec("platform", "kyc.review", "Review KYC submissions", is_sensitive=True),
    # Risk
    PermissionSpec("platform", "risk.view", "View risk flags and reports"),
    PermissionSpec("platform", "risk.review", "Platform risk review action", is_sensitive=True),
    # Agent review
    PermissionSpec("platform", "agent.view", "Review agents across agencies"),
    # Number review
    PermissionSpec("platform", "number.view", "View numbers across agencies"),
    # Call review
    PermissionSpec("platform", "call.view", "View calls across agencies"),
    # Transfer review
    PermissionSpec("platform", "transfer.view", "View transfers across agencies"),
    # Recording review
    PermissionSpec("platform", "recording.view", "View recording metadata across agencies"),
    # Integration review
    PermissionSpec("platform", "integration.view", "View integrations across agencies"),
    # Audit
    PermissionSpec("platform", "audit.view", "View audit log"),
    # Settings
    PermissionSpec("platform", "setting.view", "View platform settings"),
    PermissionSpec("platform", "setting.update", "Update platform settings"),
    # Notifications
    PermissionSpec("platform", "notification.view", "View platform notifications"),
    PermissionSpec("platform", "notification.create", "Create platform notification"),
    PermissionSpec("platform", "notification.update", "Update platform notification"),
    PermissionSpec("platform", "notification.delete", "Delete platform notification"),
    # Financial (sensitive)
    PermissionSpec(
        "platform", "payout.approve", "Approve agency payout requests", is_sensitive=True
    ),
    PermissionSpec("platform", "wallet.adjust", "Manual wallet credit/debit", is_sensitive=True),
    PermissionSpec("platform", "commission.edit", "Edit commission rates/rules", is_sensitive=True),
    # Impersonation (sensitive)
    PermissionSpec("platform", "impersonation.use", "Impersonate a tenant user", is_sensitive=True),
    # RBAC admin
    PermissionSpec("platform", "role.view", "View roles"),
    PermissionSpec("platform", "role.create", "Create roles"),
    PermissionSpec("platform", "role.update", "Update roles"),
    PermissionSpec("platform", "role.delete", "Delete roles"),
    PermissionSpec("platform", "permission.view", "View permissions"),
    PermissionSpec("platform", "permission.create", "Create permissions"),
    PermissionSpec("platform", "permission.update", "Update permissions"),
    PermissionSpec("platform", "permission.sync", "Sync permission catalog"),
]


# ---------------------------------------------------------------------------
# Agency namespace
# ---------------------------------------------------------------------------

_AGENCY: list[PermissionSpec] = [
    # Team
    PermissionSpec("agency", "team.view", "List agency team members"),
    PermissionSpec("agency", "team.create", "Invite agency team member"),
    PermissionSpec("agency", "team.delete", "Disable agency team member"),
    # Customer management
    PermissionSpec("agency", "customer.view", "View customers"),
    PermissionSpec("agency", "customer.create", "Create customer accounts"),
    PermissionSpec("agency", "customer.update", "Update customer details"),
    PermissionSpec("agency", "customer.delete", "Delete/suspend customers"),
    # Agents
    PermissionSpec("agency", "agent.view", "View agents"),
    PermissionSpec("agency", "agent.create", "Create agents"),
    PermissionSpec("agency", "agent.update", "Update agents"),
    PermissionSpec("agency", "agent.delete", "Delete agents"),
    # Numbers
    PermissionSpec("agency", "number.view", "View phone numbers"),
    PermissionSpec("agency", "number.create", "Provision phone numbers"),
    PermissionSpec("agency", "number.update", "Update phone number config"),
    PermissionSpec("agency", "number.delete", "Release phone numbers"),
    # Transfers
    PermissionSpec("agency", "transfer.view", "View transfers"),
    PermissionSpec("agency", "transfer.create", "Create transfer rules"),
    PermissionSpec("agency", "transfer.update", "Update transfer rules"),
    PermissionSpec("agency", "transfer.delete", "Delete transfer rules"),
    # Calls
    PermissionSpec("agency", "call.view", "View call records"),
    # Recordings
    PermissionSpec("agency", "recording.view", "View recording metadata"),
    PermissionSpec(
        "agency", "recording.hold", "Place a legal hold on recordings", is_sensitive=True
    ),
    # Integrations
    PermissionSpec("agency", "integration.view", "View integrations"),
    PermissionSpec("agency", "integration.create", "Connect integrations"),
    PermissionSpec("agency", "integration.update", "Update integrations"),
    PermissionSpec("agency", "integration.delete", "Remove integrations"),
    # Webhooks
    PermissionSpec("agency", "webhook.view", "View webhooks"),
    PermissionSpec("agency", "webhook.create", "Create webhooks"),
    PermissionSpec("agency", "webhook.update", "Update webhooks"),
    PermissionSpec("agency", "webhook.delete", "Delete webhooks"),
    # Notices
    PermissionSpec("agency", "notice.view", "View agency notices"),
    PermissionSpec("agency", "notice.update", "Configure agency notices"),
    # Wallet / payouts
    PermissionSpec("agency", "wallet.view", "View wallet balance and ledger"),
    PermissionSpec("agency", "payout.request", "Request a payout"),
    # Knowledge
    PermissionSpec("agency", "knowledge.view", "View knowledge bases"),
]


# ---------------------------------------------------------------------------
# Customer namespace
# ---------------------------------------------------------------------------

_CUSTOMER: list[PermissionSpec] = [
    # Team
    PermissionSpec("customer", "team.view", "List customer team members"),
    PermissionSpec("customer", "team.create", "Invite customer team member"),
    PermissionSpec("customer", "team.delete", "Disable customer team member"),
    # Billing
    PermissionSpec("customer", "billing.pay", "Submit payment for invoices"),
    # Agents
    PermissionSpec("customer", "agent.view", "View agents assigned to customer"),
    # Calls
    PermissionSpec("customer", "call.view", "View call records"),
    # Recordings
    PermissionSpec("customer", "recording.view", "View recording metadata"),
    # Risk
    PermissionSpec("customer", "risk.verify", "Submit KYC/risk verification"),
    # Knowledge
    PermissionSpec("customer", "knowledge.view", "View knowledge bases"),
    # Integrations
    PermissionSpec("customer", "integration.view", "View available integrations"),
    PermissionSpec("customer", "integration.connect", "Connect integrations"),
    # Notices
    PermissionSpec("customer", "notice.view", "View notices"),
    PermissionSpec("customer", "notice.update", "Configure notice preferences"),
]


# ---------------------------------------------------------------------------
# Full catalog (used by sync command and ensure_rbac_seeded)
# ---------------------------------------------------------------------------

PERMISSION_CATALOG: tuple[PermissionSpec, ...] = tuple(_PLATFORM + _AGENCY + _CUSTOMER)


# ---------------------------------------------------------------------------
# Role seed bundles — new permission codes
# ---------------------------------------------------------------------------

def _agency_all() -> frozenset[str]:
    """All agency-namespace codes from catalog."""
    return frozenset(s.code for s in _AGENCY)


def _customer_all() -> frozenset[str]:
    """All customer-namespace codes from catalog."""
    return frozenset(s.code for s in _CUSTOMER)


ROLE_SEED_BUNDLES: dict[str, dict] = {
    # ---- Platform roles ----
    "super_admin": {
        "namespace": "platform",
        "display_name": "Super Admin",
        "permissions": frozenset(),  # bypass — no pivot rows
    },
    "finance_admin": {
        "namespace": "platform",
        "display_name": "Finance Admin",
        "permissions": frozenset({"payout.approve", "wallet.adjust", "billing.view"}),
    },
    "compliance_kyc": {
        "namespace": "platform",
        "display_name": "Compliance / KYC",
        "permissions": frozenset({"kyc.review", "risk.view", "recording.view"}),
    },
    "support_admin": {
        "namespace": "platform",
        "display_name": "Support Admin",
        "permissions": frozenset(),
    },
    # ---- Agency roles ----
    "agency_owner": {
        "namespace": "agency",
        "display_name": "Agency Owner",
        "permissions": _agency_all(),  # all agency codes
    },
    "agency_admin": {
        "namespace": "agency",
        "display_name": "Agency Admin",
        "permissions": frozenset(
            {
                # team
                "team.view", "team.create", "team.delete",
                # customers
                "customer.view", "customer.create", "customer.update", "customer.delete",
                # agents
                "agent.view", "agent.create", "agent.update", "agent.delete",
                # numbers
                "number.view", "number.create", "number.update", "number.delete",
                # transfers
                "transfer.view", "transfer.create", "transfer.update", "transfer.delete",
                # calls & recordings
                "call.view", "recording.view",
                # integrations
                "integration.view", "integration.create",
                "integration.update", "integration.delete",
                # webhooks
                "webhook.view", "webhook.create", "webhook.update", "webhook.delete",
                # notices
                "notice.view", "notice.update",
                # knowledge
                "knowledge.view",
                # NOTE: no wallet.view, payout.request, recording.hold
            }
        ),
    },
    "agency_agent_builder": {
        "namespace": "agency",
        "display_name": "Agency Agent Builder",
        "permissions": frozenset(
            {
                "agent.view", "agent.create", "agent.update", "agent.delete",
                "transfer.view", "transfer.create", "transfer.update", "transfer.delete",
                "integration.view", "integration.create",
                "integration.update", "integration.delete",
            }
        ),
    },
    "agency_finance": {
        "namespace": "agency",
        "display_name": "Agency Finance",
        "permissions": frozenset({"wallet.view", "payout.request"}),
    },
    # ---- Customer roles ----
    "customer_owner": {
        "namespace": "customer",
        "display_name": "Customer Owner",
        "permissions": _customer_all(),  # all customer codes
    },
    "customer_admin": {
        "namespace": "customer",
        "display_name": "Customer Admin",
        "permissions": frozenset(
            {
                "team.view", "team.create", "team.delete",
                "billing.pay",
                "agent.view",
                "call.view",
                "recording.view",
                "risk.verify",
                "knowledge.view",
                "integration.view", "integration.connect",
                "notice.view", "notice.update",
            }
        ),
    },
    "customer_analyst": {
        "namespace": "customer",
        "display_name": "Customer Analyst",
        "permissions": frozenset({"agent.view", "call.view", "recording.view", "integration.view"}),
    },
}
