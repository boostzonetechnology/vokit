# Financial ledger & AgentAction source of truth

Operational mapping for SRS entity names vs V1 implementation. SRS and ADRs remain authoritative for requirements.

## LedgerEntry = CommissionEntry (VKT-004)

| SRS name | Implemented as | Notes |
|---|---|---|
| CommissionEntry | `control_plane.commission.models.LedgerEntry` | Append-only commission / wallet ledger |
| WalletLedgerEntry | Same `LedgerEntry` kinds | Holds, releases, adjustments, payouts |
| Payout / PayoutProof | `Payout`, `PayoutProof` | Status transitions allowed; **hard delete forbidden** |

Commission is ledger-centric: earn → hold → available → reserve → paid; refunds create **reversal** rows, never rewrite history.

Do **not** add a parallel `CommissionEntry` table unless an ADR reopens that decision.

## AgentAction = tool allowlist + invoke (VKT-005)

| SRS name | Implemented as | Notes |
|---|---|---|
| AgentAction | Agent `tools` JSON + `ALLOWED_TOOLS` / `assert_tools` | Allowlist enforced at write/publish time |
| Invoke path | Integrations / webhook tool invoke | Runtime may only call allowlisted tools |

There is **no** separate `AgentAction` ORM table in V1. Adding one would be a schema product decision, not a rename of the allowlist.

## Hard delete (TEN-006)

ORM `.delete()` (instance and queryset) raises `DomainError` (`hard_delete_forbidden` or `audit_immutable`) for:

- `AuditEvent`
- `LedgerEntry`, `Payout`, `PayoutProof`
- `InvoiceIndex`, `PaymentProcessorEvent`
- `KycCase`, `KycProviderEvent`

Status / soft lifecycle updates remain allowed where the domain already supports them.

Guard: `shared_kernel.hard_delete.HardDeleteForbiddenModel` (audit uses its own `assert_immutable`).

Tests: `apps/api/tests/test_hard_delete_ten006.py`.
