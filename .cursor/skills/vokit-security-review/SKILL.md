# Vokit Security Review Skill

## When to use
Use before merging authentication, authorization, tenancy, uploads, KYC, payments, webhooks, integrations, agent tools, secrets, recordings or admin overrides.

## Procedure
1. Identify trust boundaries and attacker-controlled inputs.
2. Trace authorization from route/API entry to database query/use case.
3. Verify tenant ownership is enforced server-side.
4. Check privilege escalation, IDOR/BOLA, CSRF, SSRF, injection, file upload abuse, replay and rate-limit risks.
5. Inspect secret handling and log redaction.
6. Inspect webhook signature verification and idempotency.
7. Inspect sensitive data retention/access/export/deletion behavior.
8. For payment verification images, ensure only last four digits may remain visible and prohibited authentication data is never intentionally collected.
9. Add negative/security tests.
10. Report severity, exploit path, blast radius, remediation and regression coverage.

## Required outcome
Never approve a sensitive feature solely because the happy path works. Security must be verified at the server boundary and tested against manipulated clients/requests.
