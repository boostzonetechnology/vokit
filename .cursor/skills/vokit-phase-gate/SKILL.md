---
name: vokit-phase-gate
description: Open or close a Vokit development roadmap phase. Use when starting Phase 0–20, checking exit criteria, or deciding whether the next phase may begin.
---

# Vokit Phase Gate

## When
Starting or closing a phase in `docs/execution/13-DEVELOPMENT-ROADMAP.md`.

## Open
1. Confirm the previous phase exit criteria exist in the repo (code + tests), not only in docs.
2. List SRS IDs for this phase from `docs/execution/12-FEATURE-MATRIX.md`.
3. If ADRs required by the phase are still Proposed, stop.
4. State in-scope / out-of-scope and stop conditions.

## Close
1. Run `docs/execution/11-MODULE-CHECKLIST.md` for contexts touched.
2. Require tenant/finance/recording/voice tests that apply.
3. Record residual risks and the next phase's first task.
4. Do not mark a phase complete because screens exist.

## Evidence
Use test output, health checks, migration status, or telemetry. A config file is not evidence.
