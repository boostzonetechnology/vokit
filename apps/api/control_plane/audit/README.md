# Audit

Append-only control-plane `audit_events`. Search is Super Admin only
(`GET /api/v1/platform/audit-events`). There is no edit/delete API. Payloads are
redacted; secrets, payment data, and KYC document bytes are never stored.
Overrides (KYC, risk, wallet, settings) require a reason (AUD-004).
