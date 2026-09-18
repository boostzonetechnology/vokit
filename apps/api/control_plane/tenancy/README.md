# Tenancy registry (control plane)

Physical tenant = Agency (ADR-001). Registry rows store host/port/name and a `SecretRef` key, never a password.

Provisioning is a resumable saga. A tenant is not `ready` until the tenant schema is applied and verified.

Routing is fail-closed. The browser never selects a database.

Backup/restore is tenant-scoped (`backup_tenant` / `restore_tenant`). Restoring Agency A
never opens Agency B. Canary migrations can stop after the canary (`--canary-only`).

Agency business status (`active` / `restricted` / `under_review` / `suspended` / `closed`) is separate from tenant DB status. A suspended agency stays routable so existing customer services are not cut off (BR-014). Suspend defaults force new customers/agents/numbers and payouts off (§24.1); `existing_customer_services` stays on unless Super Admin overrides. Turning that flag off rejects new production admission (`customer_services_disabled`); it does not hang up in-progress calls.

`create_agents` is status + capability (same shape as number purchase): Suspended/Closed deny everyone; non-privileged actors must be Active. Invited/Pending payouts are status-blocked (`payout_agency_blocked`) even after KYC Verified.

Platform `POST /agencies/{id}/status` and `/capabilities` require `confirm: true`. Restrict/review/suspend/close and capability overrides require `reason` (AUD-004). Restrict also sends the mandatory restriction notice (`agency.suspended`).

Commission rate changes are Super Admin only (BR-001). Optional future `rate_effective_at` keeps the live rate in `previous_commission_rate_bps` until that timestamp (ADR-010). Accrual snapshots the effective rate at settlement (BR-018).
