# Key rotation

Rotate by changing the **secret ref value** in the secret manager (or env for V1), then dual-accept old+new only if the adapter supports it. Do not put new keys in git or React.

Architecture: [ADR-008](../../adr/ADR-008-secret-management-kms-path.md) (SecretRef vs app vaults; future KMS).

## In scope

| Secret | Family | Notes |
|---|---|---|
| Stripe/Braintree webhook secrets | A — SecretRef | Dual-accept window if provider allows |
| KYC webhook secret | A — SecretRef | Replay sandbox webhook after |
| Telephony internal token | A — SecretRef | One bootstrap after |
| Recording token HMAC | A — SecretRef | One access grant after |
| Provider API / OAuth refs | A — SecretRef | Adapters resolve at call time |
| Tenant DB passwords | B — App vault | Per-tenant re-encrypt via vault |
| MFA TOTP secrets | B — App vault | Salt `identity_mfa_totp`; re-wrap all active/pending methods |
| Voice vendor API keys | B — App vault | Salt `voice_provider_api_key`; PATCH overwrite on `voice.*.api_key` |
| Session `DJANGO_SECRET_KEY` | Master | Session invalidation expected; Family B ciphertext needs re-wrap or dual-key until KMS envelope |

## After rotation

1. Replay a signed sandbox webhook.
2. One internal telephony bootstrap.
3. One recording access grant.
4. If Family B / `SECRET_KEY` changed: canary decrypt one tenant credential + one MFA method before full batch.

## MFA TOTP vault (`SECRET_KEY` or future KMS master)

1. Deploy code that can decrypt with **old** and encrypt with **new** (dual-key window), or run offline re-wrap with both keys available to the job only.
2. Batch: for each `identity_mfa_methods` row with ciphertext → decrypt → encrypt → verify TOTP round-trip on a canary user → commit.
3. Drop old key acceptance only after zero `secret_missing` / BadSignature on MFA login verify.
4. Never log TOTP secrets, recovery codes, or challenge tokens.

Until KMS lands, treat `DJANGO_SECRET_KEY` as the vault master for salts `tenant_db_pwd`, `identity_mfa_totp`, and `voice_provider_api_key`.
