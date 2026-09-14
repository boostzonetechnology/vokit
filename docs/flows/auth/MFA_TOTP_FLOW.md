# MFA TOTP flow

## Enroll (authenticated)

1. `POST /api/v1/auth/mfa/totp/enroll`
2. Response (once): `method_id`, `otpauth_uri`, `secret` — show QR / copy secret in UI
3. User enters authenticator code
4. `POST /api/v1/auth/mfa/totp/confirm` `{method_id, code}`
5. Method → `active`; first enrollment returns `recovery_codes` (store offline)

Secret is encrypted server-side; subsequent method list never returns the secret.

## Login challenge

1. Password login → `mfa_required` + `challenge_token` + methods
2. `POST /api/v1/auth/mfa/challenge/verify` `{challenge_token, method_id, code}`
3. Full session cookie

TOTP verification uses a ±1 period window (`pyotp`).

## Disable

`POST /api/v1/auth/mfa/methods/{id}/disable` with `{code, verify_method_id}` (another/same TOTP) or `{recovery_code}`.
