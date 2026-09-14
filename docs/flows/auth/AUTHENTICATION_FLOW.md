# Authentication flow

V1 browser auth uses Django session cookies + CSRF.

## Happy path (no MFA)

1. `GET /api/v1/auth/csrf` — sets CSRF cookie; returns `csrf_token`
2. `POST /api/v1/auth/login` `{email, password}` + `X-CSRFTOKEN`
3. Full session established → `GET /api/v1/auth/session` / portal `/me`
4. `POST /api/v1/auth/logout` — destroys current session

## Privileged MFA gate

Setting `security.mfa_required_privileged` (default **false**):

- When **true**, roles `super_admin`, `finance_admin`, `compliance_kyc`, `agency_owner` cannot complete password login until ≥1 **active** MFA method exists (`403 mfa_required`).
- Enroll while the flag is off (or after platform MFA reset), then enable the flag.

## MFA enrolled login

If the user has any active MFA method, password success returns a **challenge** (not a full session):

```json
{
  "mfa_required": true,
  "challenge_token": "...",
  "methods": [{"id": "...", "type": "totp|email", "email_hint": "a***@x.com"}],
  "user_id": "..."
}
```

Pre-auth does **not** satisfy `require_auth` / portal APIs (`401`).

Complete with:

- `POST /api/v1/auth/mfa/challenge/send` — email OTP for an email method
- `POST /api/v1/auth/mfa/challenge/verify` — TOTP / email OTP / recovery code → full session

See [MFA_FLOW.md](MFA_FLOW.md).

## Invite accept

`POST /api/v1/auth/invitations/accept` sets password; does not auto-login with MFA challenge (separate login).
