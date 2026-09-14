# Phase 17 security review

**Date:** 2026-09-10  
**Scope:** Authentication, RBAC, tenant routing, secrets, webhooks, uploads, payments, KYC, recordings.  
**SoT:** SRS §25–26, `16-SECURITY-STANDARDS.md`, ADR-001–008.

This is a review of the implemented control plane, not a production go-live. Staging/canary evidence is Phase 18.

## Trust boundaries

| Boundary | Finding |
|---|---|
| Browser | Untrusted. Portals call `/api/v1` only. No DSNs, secret values, or recording bytes in React. |
| Portal API | Session cookie + CSRF. Authorization is role + principal + session tenant/customer + resource. |
| Internal telephony / recording | Separate service tokens. User cookies are rejected. |
| Payment / KYC webhooks | Signature verified before parse; event-id dedup. |
| Tenant DB | Resolved from the registry after auth. Forged `tenant_id` cannot switch routing. |
| Recording plane | Metadata only in the app DB. Short-lived single-use tokens. |

## Attack paths reviewed

| Path | Mitigation | Evidence |
|---|---|---|
| Tenant escape / IDOR | Session scope; non-disclosing 403/404 | Isolation + portal tests |
| Forged tenant_id | Router binds membership tenant | `test_agency_forged_tenant_id_cannot_switch_db` |
| Session fixation | Django `login()` cycles the session key | `test_login_cycles_session_and_rate_limits` |
| Credential stuffing | Login rate limit 8 / 5 min | Same test; `rate_limited` 429 |
| Privilege escalation across namespaces | Disjoint permission catalogs | `test_agency_role_cannot_use_platform_permissions` |
| Payment / KYC spoof | HMAC before parse | Forged webhook tests → 401 |
| Webhook replay | Event-id dedup | Stripe/KYC/chargeback duplicate tests |
| Payout race | Wallet lock + reservation | `test_concurrent_payouts_cannot_over_reserve` |
| Mark paid without proof | Fail closed 409 | `test_mark_paid_is_blocked_without_proof` |
| Recording token replay / expiry | Hash + consume | Recording negative matrix |
| Artifact ID alone | Token scope required | Recording matrix |
| SSRF on webhook/URL ingest | Private-range reject | Integrations domain tests |
| Prompt/tool secret leak | Domain reject + gateway strip | Agent + tool tests |
| Audit wipe | Append-only 409 | Audit tests |
| Impersonation | Not implemented; routes 404 | `test_impersonation_is_not_implemented` |

## MFA (RBAC-008 / SEC-013) — Should

`security.mfa_required_privileged` defaults **off**.

When enabled, Super Admin / Finance / KYC / agency owner must have ≥1 active MFA method or login fails closed (`mfa_required`).

**Enrollment is implemented** (TOTP + Email OTP + recovery codes + platform `mfa.reset`):

- Flows: `docs/flows/auth/MFA_FLOW.md`
- APIs under `/api/v1/auth/mfa/*`
- Keep the flag off in lab until operators have enrolled (or use admin reset).

Production finance must not flip the flag on without an enrollment path for each privileged operator.

## Secrets (SEC-003 / SEC-015 / VKT-010)

| Layer | Status |
|---|---|
| SecretRef env | KEEP — provider keys by name only |
| Tenant DB vault | Family B signing vault |
| MFA TOTP vault | Family B (`identity_mfa_totp`) — Phase E |
| Production KMS | **Planned** in ADR-008; not implemented |

Do not replace SecretRef until ADR-008 follow-up ships. Rotation: `runbooks/key-rotation.md`.

## Impersonation (SA3-006) — Should, not implemented

`impersonation.use` exists in the platform catalog so the permission cannot be invented later as an implicit grant. No API or UI performs impersonation.

## Residual risks (do not treat as green)

- Privileged MFA UI (portal Security Settings) may still be missing; backend MFA APIs exist.
- Recording server and CRM OAuth adapters are still in-memory in this repo.
- Email is Django SMTP/locmem, not a production ESP.
- Invite accept token is still returned on the invite API for lab use.
- MySQL two-tenant isolation is skipped unless `VOKIT_MYSQL_ISOLATION=1`.
- Backup/restore and provider sandbox E2E are Phase 18.
- No live browser accessibility audit tool was run; portals received a WCAG 2.1 AA structural pass (landmarks, labels, focus, contrast, skip link).

Critical unresolved MFA/backup/sandbox items still **block production**, not Phase 17 close.
