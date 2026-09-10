# Vokit Cursor Workflows

Repeatable agent workflows. Invoke by name in chat (example: “Run workflow **implement-feature** for Phase 6 invoices”).

Each workflow assumes the authority order in the Cursor Master Guide.

---

## WF-00 Baseline

**Use:** New chat, new engineer, or before any HIGH work.

1. Read `docs/execution/00-COMPLETE-EXECUTION-PLAN.md`.
2. Inspect repo: list `apps/`, `packages/`, `docs/adr/`.
3. Summarize: what exists, what is missing, which phase is current.
4. List Decided questions that affect the next task.
5. Do not write product code.

**Output:** current architecture map + recommended next phase.

---

## WF-01 Phase gate

**Use:** Starting or closing a roadmap phase.

1. Open `13-DEVELOPMENT-ROADMAP.md` for the phase.
2. Confirm previous phase exit criteria are met in code/tests.
3. List SRS IDs in scope.
4. If HIGH decisions are open, draft ADR and stop.
5. On close: run module checklist + required tests; write residual risks.

**Skill:** `vokit-phase-gate`

---

## WF-02 Implement feature

**Use:** Any vertical slice after proceed.

1. Identify SRS IDs from `12-FEATURE-MATRIX.md`.
2. Architecture review template (`vokit-architecture-review`).
3. Design state machine and ownership.
4. Implement domain → application → infra → API.
5. Add tests including tenant negatives if tenant-owned.
6. Add observability.
7. Only then React, if the slice has UI.
8. File the task report.

**Skill:** `vokit-implement-feature`

Never implement tenant router, recordings, billing, or auth as a “quick path.”

---

## WF-03 Tenant isolation check

**Use:** Any tenant-owned API, job, or query.

Prove:

- A cannot read/write B
- Forged tenant_id does not switch routing
- Same object ID resolves only in current tenant
- Worker cannot cross tenants
- Disabled/missing tenant fails closed
- Outage does not fall back
- Pool reuse cannot leak tenant context

**Skill:** `vokit-tenant-db-architecture`

---

## WF-04 Financial integrity check

**Use:** Payments, invoices, commission, payouts, refunds, chargebacks.

Prove:

- Ledger is insert-only
- Duplicate webhook does not double-settle
- Hold timestamps are per entry
- Reservation is atomic
- Chargeback uses compensating entries
- Agency cannot see payout proof
- Reports read ledger, not UI math

---

## WF-05 Voice contract check

**Use:** Any Django telephony or Pipecat/Edge change.

1. Diff frozen internal paths and Edge HTTP API.
2. Confirm admission fail-closed.
3. Confirm tools go through Django.
4. Confirm no secrets in bootstrap prompts.
5. Confirm media sample rate / μ-law contract unchanged unless ADR.
6. Compatibility test + rollback note.

---

## WF-06 Recording access check

**Use:** Playback, ingest, retention, deletion.

Run the recording negative matrix in the QA plan.  
Raw bytes must not enter Django static/media or logs.

**Skill:** `vokit-recording-data-plane`

---

## WF-07 Security review

**Use:** Auth, uploads, webhooks, KYC provider keys/webhooks, admin overrides, public infra.

Threat-model: tenant escape, IDOR, SSRF, secret leak, replay, priv-esc, malicious webhook, poisoned job, exfil, DoS.

**Skill:** `vokit-security-threat-model`

---

## WF-08 UI slice

**Use:** Portal screens.

1. Confirm API contract exists and is authorized.
2. Implement against DTOs only.
3. Exercise empty/error/forbidden/success.
4. Verify in browser when tools exist; otherwise state the gap.
5. Do not add client-side permission engines.

---

## WF-09 Release gate

**Use:** Before merge to main or deploy.

Walk `21-RELEASE-CHECKLISTS.md` and `71-release-gates` rule.  
HIGH changes need runbook + rollback + negatives.

**Skill:** `vokit-production-readiness`

---

## WF-10 Incident

**Use:** Production/staging incident.

Contain → preserve evidence → blast radius → mitigate → verify → communicate → RCA → corrective action.  
Never destroy evidence to make dashboards green.

**Skill:** `vokit-incident-response`

---

## WF-11 Scale proposal

**Use:** Someone wants a new service, replica, shard, or extra tenant host.

Require measured bottleneck, capacity numbers, failure mode, rollout, ADR.  
Reject speculative extraction.

**Skill:** `vokit-capacity-planning`

---

## Suggested chat prompts

```text
Run WF-00 Baseline. Do not write code.

Run WF-01 Phase gate for Phase 3. Report exit gaps.

Run WF-02 Implement feature for TEN-001 tenant router. Stop if ADR-001 is not Accepted.

Run WF-03 Tenant isolation check on the files you just changed.

Run WF-09 Release gate for this branch.
```
