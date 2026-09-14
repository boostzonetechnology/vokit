# ADR-008 — Secret management layers & future KMS path

**Status:** Accepted  
**Date:** 2026-09-14  
**SRS refs:** SEC-003, SEC-014, SEC-015, INT-002  
**Jira:** VKT-010  

---

## Context

Vokit already stores secrets without returning plaintext to clients:

1. **`SecretRef`** (`shared_kernel/secrets.py`) — models store a key name; Phase 1 resolves from **env only**.
2. **Application vaults** (Django `signing` + `SECRET_KEY`) — ciphertext in control-plane tables:
   - Tenant DB passwords — `tenant_db_credentials` / `DjangoTenantDbVault`
   - MFA TOTP secrets — `identity_mfa_methods.secret_ciphertext` / `MfaSecretVault`

VKT-010 remaining work asked for a production KMS/secret-manager decision. Replacing `SecretRef` or migrating every provider key in this phase would be high-risk and is **out of scope**.

---

## Decision

### 1. Keep two secret families (do not collapse)

| Family | What | Storage | Resolve |
|---|---|---|---|
| **A — SecretRef** | Provider API keys, webhook signing secrets, OAuth refresh refs, internal service tokens | Key **name** in DB / config | Runtime resolve via provider (`env` today) |
| **B — App vault** | Per-row secrets that must live next to the row (tenant DB pwd, MFA TOTP) | Ciphertext in MySQL | Decrypt in process with vault salt + master key |

Never put MFA TOTP plaintext or tenant DB passwords into env `SecretRef` keys. Never put long-lived provider API keys as app-vault ciphertext without a rotation story.

### 2. V1 provider stays `env`

`SecretRef(provider="env")` remains the only supported provider until a follow-on implementation story. Do **not** invent partial AWS/GCP adapters in application code without this ADR’s migration steps.

### 3. Target production adapters (choose at deploy; one primary)

Accepted options for **Family A** when we leave env-only:

| Provider id (future) | Use when |
|---|---|
| `aws_secretsmanager` or `aws_kms` + SM | AWS-hosted production |
| `gcp_secretmanager` | GCP-hosted production |
| `hashicorp_vault` | Self-managed / multi-cloud |

Envelope pattern for **Family B** when KMS lands:

1. Data key encrypts row ciphertext (or keep Django signing payload).
2. KMS wraps the data key / master material that replaces raw reliance on a single long-lived `DJANGO_SECRET_KEY` for vault salts.
3. App never logs plaintext, data keys, or KMS plaintext responses.

Exact cloud product is an **ops choice**; domain code must depend only on a `SecretBackend` / `VaultBackend` port.

### 4. MFA vault is in Family B (done for V1)

- Salt: `identity_mfa_totp` (distinct from `tenant_db_pwd`).
- Ciphertext column only; OTP/recovery codes remain hashes, not vaulted.
- Compatible with Google Authenticator / Authy via `otpauth` + `pyotp` (RFC 6238) — library choice is orthogonal to KMS.

### 4b. Voice vendor API keys (Family B addendum — 2026-09-14)

Owner decision: Super Admin stores STT/TTS/LLM vendor API keys in `platform_settings` as **ciphertext**, not env `SecretRef` and not plaintext JSON.

- Salt: `voice_provider_api_key` (distinct from MFA and tenant DB).
- PATCH `/api/v1/platform/settings` accepts plaintext once; encrypt before persist.
- GET never returns the key (`value` null; `has_value` only).
- Decrypt in-process for Pipecat bootstrap and TTS voice-list adapters only.
- Rotation: PATCH overwrite. `DJANGO_SECRET_KEY` rotation invalidates these rows (same as other Family B vaults) until KMS envelope.
- React / logs / audit `after_summary` must not contain plaintext.

This is a **narrow exception** to “no vault UI for provider keys”: there is no dedicated vault product UI in this slice — keys ride the existing settings PATCH with `secret=true`. Webhook/OAuth/internal tokens remain Family A SecretRef.

### 5. Explicit non-goals (this ADR)

- No replacement of existing `SecretRef` rows or env keys (except voice STT/TTS/LLM live selection, which now reads platform settings).
- No dedicated third-party vault product UI.
- No dual-cloud secret backends in V1.
- No storing KYC document bytes (ADR-005).

---

## Migration / rotation plan (when implementing KMS)

Follow expand → dual-read → contract:

1. **Port** — Introduce `SecretBackend.resolve(ref)` and optional `VaultBackend.encrypt/decrypt` behind env implementations that match today’s behavior.
2. **Config** — Add provider enum values; reject unknown providers fail-closed.
3. **Dual-read** — For each Family A secret: try new backend, fall back to env during cutover window; metric on fallback.
4. **Family B re-wrap** — Batch job: decrypt with old master → encrypt with KMS-wrapped master; per-row progress; pause/resume; never delete old ciphertext until verify pass.
5. **Cutover** — Disable env fallback; alert on `secret_missing` / BadSignature spikes.
6. **Rotate** — Documented in `docs/execution/runbooks/key-rotation.md` (webhook, telephony, recording HMAC, tenant vault, MFA vault, `DJANGO_SECRET_KEY`).

Rollback: re-enable env / previous master key material; leave new ciphertext columns until stable (do not drop).

---

## Consequences

Positive:

- Clear SoT for what lives in env vs DB ciphertext.
- MFA TOTP already matches tenant vault family.
- KMS work is bounded and reversible.

Trade-offs:

- `DJANGO_SECRET_KEY` rotation still invalidates sessions **and** requires Family B re-wrap until KMS envelope lands.
- Operators must keep env secrets and vault master material in the deploy secret store (not git).

---

## Required follow-up (implementation stories — not this phase)

1. Implement chosen cloud `SecretBackend` behind feature flag.
2. Re-wrap tenant + MFA vaults under KMS envelope.
3. Audit that every provider credential path uses `SecretRef` exclusively (no plaintext columns).
4. Staging evidence: rotate one webhook secret + one MFA re-wrap canary.

---

## Evidence (current)

- `apps/api/shared_kernel/secrets.py`
- `apps/api/control_plane/tenancy/infrastructure/vault.py`
- `apps/api/control_plane/identity/infrastructure/mfa_vault.py`
- `apps/api/control_plane/platform_settings/infrastructure/voice_vault.py`
- `docs/execution/runbooks/key-rotation.md`
- `apps/api/tests/test_secret_ref.py`
- `apps/api/tests/test_mfa_vault.py`
