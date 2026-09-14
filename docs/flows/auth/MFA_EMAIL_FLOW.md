# MFA Email OTP flow

## Enroll (authenticated)

1. `POST /api/v1/auth/mfa/email/enroll`
2. Response: `method_id`, `challenge_token`, `expires_in`
3. User receives 6-digit code by email (Django mailer; not persisted in notification delivery rows)
4. `POST /api/v1/auth/mfa/email/confirm` `{method_id, challenge_token, code}`
5. Method → `active`; may return `recovery_codes` on first enrollment

Email target is the user's account email.

## Login challenge

1. Password login → challenge + email method (with `email_hint`)
2. `POST /api/v1/auth/mfa/challenge/send` `{challenge_token, method_id}`
3. `POST /api/v1/auth/mfa/challenge/verify` `{challenge_token, method_id, code}`

OTP TTL default 10 minutes; max 5 attempts per challenge (`429 mfa_challenge_locked` when exceeded).

## Rate limits (SEC-008)

- **Send** (`email/enroll`, `challenge/send`): 5 / 10 minutes per IP+scope → `429 rate_limited`
- **Verify failures** (confirm / challenge verify): 10 / 5 minutes per IP+scope → `429 rate_limited`
- Shared cache required for multi-worker (see [MFA_FLOW.md](MFA_FLOW.md))

## Notes

- Replay of a consumed enroll challenge fails.
