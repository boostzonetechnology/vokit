# Vokit Security Standards

**SoT:** SRS §25–26, SEC-*, PRIV-*, RBAC-*, AUD-*, TEN-*

## 1. Trust boundaries

| Boundary | Trust |
|---|---|
| Browser | Untrusted |
| Portal API | Authenticated, not authorized until RBAC+scope |
| Internal telephony token | Trusted service, still no tenant inference from caller headers |
| Payment webhooks | Untrusted until signature verified |
| Tenant DB | Trusted only after registry resolve |
| Recording server | Separate domain; no tenant DB credentials |
| Pipecat | Media plane; no tenant OAuth |

## 2. Authentication

- Secure session cookies: HttpOnly, Secure, SameSite appropriate (SEC-006)
- CSRF on browser mutations (SEC-007)
- Privileged MFA before production finance (SEC-013 / RBAC-008). Setting `security.mfa_required_privileged` fails closed when on; enrollment is not shipped yet.
- Disable user → revoke sessions (RBAC-007)
- Internal paths use service tokens, not user cookies
- No secrets in React bundles

## 3. Authorization

Evaluate identity + role namespace + tenant + customer + resource + capability.

Super Admin is the only cross-tenant actor. Sensitive overrides need explicit permission + reason + audit.

Customer-owned resources always require customer scope, even for agency users (subject to AG5-003 policy).

## 4. Tenancy

- Server-resolved routing only
- Fail closed
- Non-disclosing not-found
- Jobs carry immutable tenant context
- Connection pools never cross tenant identity

## 5. Secrets

Store secret references. Encrypt at rest via approved secret manager/env.

Rotate provider credentials and webhook secrets without data loss (SEC-014).

Never log secrets, DSNs, session tokens, refresh tokens, or signing keys.

## 6. Payments and KYC

- Hosted/tokenized fields; no raw CSC (SEC-004)
- No full PAN storage
- Card images (customer payment-risk): last-four only; reject otherwise
- Agency KYC API keys: secret refs only; never in React or tenant DBs
- Agency KYC documents stay at the provider; do not make Vokit the vault
- KYC webhook signature before parse; redact identity payloads in logs
- Payout proof remains private Super Admin evidence (unrelated to KYC files)

## 7. Uploads

Type/size policy. Malware scan where infrastructure permits (SEC-011).  
No SSRF via knowledge URL fetch without allowlist/block private ranges.

## 8. Webhooks

Inbound: verify signature before parse; dedup event ID.  
Outbound: tenant signing secret; no secret payloads; bounded retry.

## 9. Recordings and transcripts

Separate plane. Short-lived access. Audit.  
Never put raw audio or full transcripts in logs/APM.

## 10. Rate limits

Login, OTP, reset, payout, webhook replay, expensive search/export (SEC-008).

## 11. Transport

TLS everywhere in production, including tenant MySQL where policy requires.

## 12. Privacy / retention

Configurable retention; legal hold; deletion workflow with finance/KYC exceptions (PRIV-004–005).  
Jurisdictions are not enabled without legal review (SRS governance).

## 13. Threat tests required before prod

Tenant escape, IDOR, forged tenant_id, webhook replay (payment and KYC), payout race, recording token replay, KYC status spoof without signature, leaked KYC API keys, SSRF on URL ingest, session fixation, privilege escalation across namespaces.
