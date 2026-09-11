# Vokit Execution Pack

Implementation operating system for Vokit V1. This pack does **not** replace the product source of truth.

## Authority order

1. [`docs/Vokit_V1_Agency_Platform_SRS_v1.0.md`](../Vokit_V1_Agency_Platform_SRS_v1.0.md) — **the one and only product source of truth**
2. [`docs/OPEN-QUESTIONS.md`](../OPEN-QUESTIONS.md) — Decided answers Q-001 through Q-016
3. [`docs/adr/`](../adr/) — ADR-001 through ADR-006
4. Existing Pipecat / SIP Edge / Asterisk wire contracts
5. This pack
6. Current implementation

If this pack and the SRS conflict, **the SRS wins**.

## Documents in this pack

| Doc | Purpose |
|---|---|
| [00 Complete Execution Plan](00-COMPLETE-EXECUTION-PLAN.md) | Architecture maps, method, Gate 0 → scale |
| [03 System Architecture](03-SYSTEM-ARCHITECTURE.md) | Control / tenant / recording / voice planes |
| [04 Database Design](04-DATABASE-DESIGN.md) | Physical ownership + ERD |
| [06 API Contracts](06-API-CONTRACTS.md) | Portal, internal telephony, webhook envelopes |
| [09 Folder Structure](09-FOLDER-STRUCTURE.md) | Target repo layout |
| [10 Coding Standards](10-CODING-STANDARDS.md) | Language and layer rules |
| [11 Module Checklist](11-MODULE-CHECKLIST.md) | Bounded-context definition of done |
| [12 Feature Matrix](12-FEATURE-MATRIX.md) | SRS ID → module → phase |
| [13 Development Roadmap](13-DEVELOPMENT-ROADMAP.md) | Phase sequence and exit criteria |
| [14 Cursor Master Guide](14-CURSOR-MASTER-GUIDE.md) | How Cursor must work in this repo |
| [15 Cursor Workflows](15-CURSOR-WORKFLOWS.md) | Repeatable agent workflows |
| [16 Security Standards](16-SECURITY-STANDARDS.md) | Auth, tenancy, secrets, privacy |
| [17 QA Testing Plan](17-QA-TESTING-PLAN.md) | Test strategy and negative matrices |
| [18 Local Development](18-LOCAL-DEVELOPMENT.md) | Local stack |
| [19 Deployment Operations](19-DEPLOYMENT-OPERATIONS.md) | Runbooks and SRE ops |
| [20 Production Deployment](20-PRODUCTION-DEPLOYMENT.md) | Rollout and rollback |
| [21 Release Checklists](21-RELEASE-CHECKLISTS.md) | Per-release gates |
| [22 Production Checklist](22-PRODUCTION-CHECKLIST.md) | Environment readiness |
| [23 Final Production Checklist](23-FINAL-PRODUCTION-CHECKLIST.md) | Launch go/no-go |
| [24 Phase 17 security review](24-PHASE-17-SECURITY-REVIEW.md) | Auth/RBAC/tenancy/webhook/recording review |
| [25 Capacity worksheet](25-CAPACITY-WORKSHEET.md) | Pre-scale estimates; no speculative replicas |
| [26 Phase 19 evidence](26-PHASE-19-EVIDENCE.md) | Lab ready / live No-Go pack |
| [Known gaps](../known-gaps/README.md) | Open SRS-vs-code module gaps (backlog) |
| [Runbooks](runbooks/README.md) | Staging/ops procedures (backup, canary, P0 isolation) |

## Removed as duplicates (already covered)

| Removed | Now lives in |
|---|---|
| `docs/ADR-001/002/003.md` stubs | `docs/adr/` only |
| Project charter | Execution plan §0–8 + OPEN-QUESTIONS + ADRs |
| Product specs | SRS |
| Standalone ERD file | [04 Database Design](04-DATABASE-DESIGN.md) §§12–13 |
| UI implementation guide | SRS portal chapters + Q-007 + folder structure |
| User flows | SRS §§6, 10–11, 24 + OPEN-QUESTIONS |

Owner proceed was given 2026-09-10. Phases 0–19 (gate) are complete. Live launch is No-Go. Phase 20 waits for a live GO.
