# Flows

Operational / product flow docs for implemented backend paths.

These describe **what runs today**, not backlog wishes. SRS and ADRs remain authoritative for requirements and decisions.

| Doc | Flow |
|---|---|
| [Agency create + MySQL provisioning](AGENCY-CREATE-MYSQL.md) | Super Admin creates an agency, provisions a dedicated MySQL DB/user, invites the owner |
| [Super Admin Customers](CUSTOMER-SUPER-ADMIN.md) | SA3 create/invite/status/usage/minutes + open deferrals |
| [Roles & permissions (RBAC)](RBAC-ROLES-PERMISSIONS.md) | Dynamic DB roles/permissions, sync, invite-by-slug, super_admin bypass (ADR-007) |
| [Ledger & AgentAction SoT](LEDGER-AND-AGENT-ACTION-SOT.md) | LedgerEntry = CommissionEntry; AgentAction = tool allowlist; TEN-006 hard-delete |
| [Authentication](auth/AUTHENTICATION_FLOW.md) | CSRF + session login/logout; MFA challenge gate |
| [MFA overview](auth/MFA_FLOW.md) | TOTP + Email OTP enroll/verify/disable/reset |
| [MFA TOTP](auth/MFA_TOTP_FLOW.md) | Authenticator enroll + login verify |
| [MFA Email OTP](auth/MFA_EMAIL_FLOW.md) | Email OTP enroll + login verify |
| [ADR-008 secrets / KMS](../adr/ADR-008-secret-management-kms-path.md) | SecretRef vs app vaults; MFA + tenant vault; future KMS |
