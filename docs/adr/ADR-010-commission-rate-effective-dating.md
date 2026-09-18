# ADR-010 — Commission rate effective dating

**Status:** Accepted  
**Date:** 2026-09-18  
**SRS refs:** SA2-003, BR-001, BR-018, AUD-004  
**Jira:** VKT-021  

---

## Context

SA2-003 requires Super Admin to set or change an agency commission rate with an
effective date. BR-018 requires historical commission entries to keep the rate
snapshot used at settlement. The control-plane `Tenant` row previously stored a
single `commission_rate_bps` applied immediately (`rate_effective_at = now`).

A future effective date cannot work with one rate column: accrual would either
apply the new rate too early or lose the live rate.

## Decision

Keep one pending pair plus the live predecessor on the Agency tenant row:

- `commission_rate_bps` — the scheduled (or already live) rate
- `rate_effective_at` — when that rate becomes live
- `previous_commission_rate_bps` — the rate used until `rate_effective_at`

`effective_commission_rate_bps` at time `at`:

- if `rate_effective_at` is null or `at >= rate_effective_at` → `commission_rate_bps`
- else → `previous_commission_rate_bps`

Rules:

- Accrual uses the effective rate at `settled_at` for both amount and
  `rate_bps_snapshot`. Ledger rows are never rewritten (BR-018).
- Omitting `rate_effective_at` applies immediately (`now`).
- A provided timestamp earlier than `now` is rejected (past dating would imply
  rewriting history).
- A new change replaces any unused pending rate. `previous_*` is the rate that
  is effective at the change timestamp, not the discarded pending value.
- Agency users cannot change the rate (BR-001). Super Admin `reason` is
  required (AUD-004).
- V1 stores **one** pending change, not a multi-step schedule.

Create agency copies the initial rate into both current and previous, with
`rate_effective_at = now`.

## Consequences

Positive:

- Future dating without a second ledger or rate-history table.
- Snapshots stay immutable.

Trade-offs:

- Only one future change at a time.
- Directory/detail must expose `previous_commission_rate_bps` so Super Admin
  can see live vs scheduled.

## Rollback

Stop writing `previous_commission_rate_bps`. Accrual can fall back to
`commission_rate_bps` only. Do not rewrite ledger snapshots. The column may
remain unused.

## Change rule

Do not let agency principals edit commission rates. Do not backdate
`rate_effective_at`. Do not mutate historical `rate_bps_snapshot` values.
