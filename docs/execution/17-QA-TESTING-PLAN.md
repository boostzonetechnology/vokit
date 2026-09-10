# Vokit QA Testing Plan

**SoT:** SRS §31, bootstrap testing section, NFR-005

## 1. Strategy

| Layer | What it proves |
|---|---|
| Domain | State machines, money math, hold/reversal |
| Application | Use-case authorization + transactions |
| API contract | Envelope, codes, pagination, idempotency |
| Tenant isolation | Negative matrix |
| Adapter | Stripe/Braintree/telephony normalized |
| Worker | Routing reconstruction, retry, poison |
| Recording | Access + ingest + orphans |
| E2E | SRS §31.1 journeys |
| Security | Threat tests |
| Ops | Backup restore, failover fail-closed |

React tests cover presentation and error mapping, not commission math.

## 2. Minimum tenant negative matrix

For every tenant-owned feature:

1. Tenant A cannot read Tenant B
2. Tenant A cannot write Tenant B
3. Forged tenant_id cannot change DB routing
4. Same object ID in two tenant DBs resolves only in current tenant
5. Worker jobs cannot cross tenant boundaries
6. Disabled tenant cannot be routed
7. Missing tenant DB mapping fails closed
8. Tenant DB outage never falls back to another tenant
9. Connection pool reuse cannot leak tenant context

## 3. Minimum recording negative matrix

1. Tenant A cannot access Tenant B recordings
2. Customer cannot access recordings outside its scope
3. Expired signed access fails
4. Replayed tokens fail per policy
5. Artifact ID alone is insufficient
6. Deleted / retained / legal-held states follow policy
7. Recording-server outage does not corrupt call metadata
8. Orphan recordings and orphan metadata are detectable

## 4. Financial test battery (release-blocking)

- Duplicate payment webhook → one settle, one commission
- Commission snapshot survives later rate change (Appendix C Ex 5)
- Independent holds (Ex 2)
- Refund during hold (Ex 3)
- Chargeback after payout → negative wallet, history intact (Ex 4)
- Two concurrent payouts cannot over-reserve
- Agency cannot fetch payout proof
- Mark Paid blocked when proof mandatory and missing
- Chargeback freeze disables agents immediately

## 5. Voice test battery

- Unpublished/paused agent not routable
- Out-of-minutes: overage vs grace vs end
- Bootstrap fail-closed if Django down
- Tool secrets never returned to Pipecat prompt
- Transfer poll terminal states
- Inbound + outbound lab call
- Voicemail artifact created without failing the call record

## 6. Risk / KYC

- Payout rejected when KYC not Verified or status unknown
- Duplicate KYC webhook does not flip status twice incorrectly
- Unsigned/forged KYC webhook rejected
- Agency cannot mark itself Verified via API
- Super Admin override is audited
- No KYC document bytes persisted in Vokit fixtures
- Over-exposed card image rejected (customer payment-risk)
- Banned customer create returns generic ineligible
- Agency cannot approve its own customer payment verification

## 7. Environments

| Env | Data | Providers |
|---|---|---|
| Local | Synthetic two-tenant fixture | Mocks + optional sandbox |
| CI | Ephemeral MySQL × control + 2 tenants | Mocks |
| Staging | Canary agency | Processor + telephony sandbox |
| Prod canary | One real tenant | Live with enhanced monitoring |

## 8. Exit for V1

SRS §31.1 and §31.2 are both green, plus both negative matrices, plus backup/restore evidence.

Phase 18 evidence (lab/CI, sandbox adapters): `tests/test_backup_restore.py`, `tests/test_staging_sandbox_e2e.py`, `tests/test_provision_migrate.py`. Live provider keys and a dated restore drill remain Phase 19 go/no-go (`26-PHASE-19-EVIDENCE.md`, `tests/test_production_readiness.py`).
