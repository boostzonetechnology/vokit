# MFA flow (overview)

SRS: SEC-013 / RBAC-008 (Should). Product decision: **TOTP and/or Email OTP**.

## Policy

| Rule | Behavior |
|---|---|
| Methods | Users may enable TOTP and/or Email OTP |
| Privileged flag | When `security.mfa_required_privileged=true`, privileged roles need ≥1 active method |
| Last method | Cannot disable the last active method while flag is on for a privileged role (`409 mfa_last_method`) |
| Recovery | Hashed recovery codes issued on first enrollment; regenerate with step-up |
| Admin reset | `POST /api/v1/platform/users/{id}/mfa/reset` + `reason` (perm `mfa.reset`) |

## Endpoints

| Method | Path | Auth |
|---|---|---|
| GET | `/api/v1/auth/mfa/methods` | Full session |
| POST | `/api/v1/auth/mfa/totp/enroll` | Full session |
| POST | `/api/v1/auth/mfa/totp/confirm` | Full session |
| POST | `/api/v1/auth/mfa/email/enroll` | Full session |
| POST | `/api/v1/auth/mfa/email/confirm` | Full session |
| POST | `/api/v1/auth/mfa/methods/{id}/disable` | Full session + step-up |
| POST | `/api/v1/auth/mfa/recovery/regenerate` | Full session + step-up |
| POST | `/api/v1/auth/mfa/challenge/send` | Challenge token |
| POST | `/api/v1/auth/mfa/challenge/verify` | Challenge token |
| POST | `/api/v1/platform/users/{id}/mfa/reset` | Platform `mfa.reset` |

Step-up for disable/regenerate: TOTP `code` + `verify_method_id`/`method_id`, or `recovery_code`.

## Rate limits (SEC-008 / Phase C)

| Endpoint family | Default | Window | Key |
|---|---|---|---|
| Email OTP **send** (`email/enroll`, `challenge/send`) | 5 | 10 min | IP + action + user/token |
| MFA **verify** failures (confirm / challenge verify) | 10 | 5 min | IP + action + user/token |
| Per-challenge attempts | 5 | challenge TTL | DB `MfaChallenge.attempts` |
| Challenge / OTP TTL | 10 min | — | `expires_at` |

Login password rate limit remains separate (8 / 5 min).

### Multi-worker note

Counters use Django `CACHES`. Default `LocMemCache` is **per process**. For multi-worker or multi-host, configure a shared cache (Redis) so SEC-008 limits are coherent. Redis is already used for Celery; pointing `CACHES` at Redis is the production plan — no MFA code change required.

## Secrets

- TOTP secrets: **app-vault Family B** (ADR-008) — Django signing, salt `identity_mfa_totp`, ciphertext on `identity_mfa_methods`. Same pattern as tenant DB vault; **not** `SecretRef`/env.
- OTP / recovery codes stored as SHA-256 hashes only.
- Secrets never logged (`otp`, `totp`, `recovery_code`, `challenge_token` redacted).
- Rotation: `docs/execution/runbooks/key-rotation.md` (MFA re-wrap when `SECRET_KEY` / KMS master changes).

## Details

- [MFA_TOTP_FLOW.md](MFA_TOTP_FLOW.md)
- [MFA_EMAIL_FLOW.md](MFA_EMAIL_FLOW.md)
- [AUTHENTICATION_FLOW.md](AUTHENTICATION_FLOW.md)
