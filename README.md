# Vokit

Agency-first AI voice platform. V1 is a greenfield Django + MySQL control/tenant plane with React portals, plus the existing Pipecat / SIP Edge / Asterisk realtime stack.

## Product source of truth

**`docs/Vokit_V1_Agency_Platform_SRS_v1.0.md` is the one and only product source of truth.**

Supporting decisions: `docs/OPEN-QUESTIONS.md` (Q-001–Q-016) and `docs/adr/`.

## Implementation pack

**[docs/execution/README.md](docs/execution/README.md)**

Start with the [complete execution plan](docs/execution/00-COMPLETE-EXECUTION-PLAN.md) and the [development roadmap](docs/execution/13-DEVELOPMENT-ROADMAP.md).

Cursor method: `MASTER-CURSOR-BOOTSTRAP.md` and `.cursor/`.

Do not implement application code until the owner says **proceed**.

## Current repo

| Area | State |
|---|---|
| SRS + open questions | Baseline; Q-001–Q-016 decided |
| ADRs 001–006 | Accepted in `docs/adr/` |
| Django API | Phases 0–19 gate in `apps/api` (live launch No-Go until dated attestations) |
| React portals | Must screens + core WCAG pass in `apps/web-*` |
| `packages/pipecat-voice` | Existing media peer |
| `packages/vokit-sip-edge` | Existing SIP edge |
| `deploy/asterisk` | Lab configs |
