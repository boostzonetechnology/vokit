# Vokit Target Folder Structure

Do not create this tree until Gate 0 **proceed**. This is the contract for Phase 1.

```text
vokit/
  docs/
    Vokit_V1_Agency_Platform_SRS_v1.0.md    # product SoT
    OPEN-QUESTIONS.md
    adr/                                    # canonical ADRs
    execution/                              # this pack
      runbooks/                             # staging/ops procedures (Phase 18)
      26-PHASE-19-EVIDENCE.md               # lab ready / live No-Go pack
  .cursor/
    rules/
    skills/
  apps/
    api/                                    # Django modular monolith
      manage.py
      pyproject.toml
      config/                               # settings, urls, celery, asgi
        settings/
          base.py
          local.py
          production.py
      control_plane/                        # Django apps: identity, tenancy, audit, ...
      tenant/                               # Django apps bound to tenant DB
      shared_kernel/                        # IDs, money, errors, time, logging
      providers/                            # Stripe, Braintree, telephony adapters
      tests/
    web-platform/                           # React Super Admin
    web-agency/
    web-customer/
    recording/                              # recording data-plane service
  packages/
    pipecat-voice/                          # existing — do not rewrite casually
    vokit-sip-edge/                         # existing
    web-ui/                                 # shared presentation primitives only
    api-types/                              # generated OpenAPI types (optional)
  deploy/
    asterisk/                               # existing
    recording/
    mysql/
    compose/                                # local only
  .github/workflows/                        # CI
```

## Django module layout (inside `apps/api`)

Each bounded context:

```text
<context>/
  domain/           # entities, policies, state machines
  application/      # use cases
  infrastructure/   # repositories, ORM models, adapters
  api/              # views, serializers, urls
  tests/
```

Forbidden shortcuts:

- `models.py` as the only workflow home
- portal React importing Django types via unsafe sharing
- putting recordings under `apps/api/media/`

## Existing packages stay

`packages/pipecat-voice`, `packages/vokit-sip-edge`, and `deploy/asterisk` remain the realtime stack. ADR-006 keeps Edge `{to}` unchanged; Django owns queue hunt and SIP-client mapping.

Canonical ADRs live only in `docs/adr/`.
