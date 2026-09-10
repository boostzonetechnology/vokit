# Vokit Feature Matrix

Maps SRS requirement families to module, portal, phase, and priority.

Legend: **P** Platform · **A** Agency · **C** Customer · **R** Runtime · **W** Worker

| Feature | IDs | Module | Surfaces | Phase | Pri |
|---|---|---|---|---|---|
| Tenant isolation | TEN-001–006 | tenancy, identity | All | 3 | Must |
| Hierarchical ownership | SRS §3, TEN-002 | customers, calls | All | 4 | Must |
| Membership model | Q-001, RBAC-* | identity | P/A/C | 2 | Must |
| Platform RBAC | SA18-*, SEC-002 | identity | P | 2 | Must |
| Agency create/invite | SA2-001, §6.1 | tenancy | P/A | 4 | Must |
| Agency status/capabilities | SA2-004/005, BR-012–014 | tenancy | P | 4 | Must |
| Commission rate + snapshot | SA2-003, BR-001, BR-018 | commission | P | 7 | Must |
| Customer CRUD | SA3-*, AG2-* | customers | P/A | 4 | Must |
| Customer reassignment | Q-006, Q-016 | tenancy, customers | P | later | Deferred |
| Agency KYC (external) | KYC-*, AG12-*, SA4-*, Q-015 | kyc | P/A | 5 | Must |
| Plans + versioning | PLAN-*, SA11-*, Q-004 | billing | P/A/C | 6 | Must |
| Subscriptions/invoices/pay | §10, CU5-*, SA12-* | billing | P/A/C | 6 | Must |
| Stripe + Braintree | Q-011, SEC-004 | billing adapters | W | 6 | Must |
| Minutes + overage + grace | Q-003, PLAN-002–004, CALL-002 | billing, calls | C/R | 6/11 | Must |
| Top-ups | CU4-003, PLAN-003 | billing | C | 6 | Must |
| Commission hold 15d | BR-003–005, WAL-001 | commission | A/P/W | 7 | Must |
| Wallet ledger | WAL-*, BR-020 | commission | A/P | 7 | Must |
| Payout request/process | AG11-*, SA13-*, BR-006–010 | commission | A/P | 7 | Must |
| Private proof + receipt | BR-009–010 | commission | P/A | 7 | Must |
| Negative wallet | WAL-005, Appendix C | commission | A/P | 7 | Must |
| Payment risk + verification | Risk module | risk | P/A/C | 8 | Must |
| Chargeback freeze + ban | Risk 14–18 | risk, agents | P/A/R | 8 | Must |
| Agent builder | AGT-*, AG3-*, SA5-* | agents | P/A/C | 9 | Must |
| Templates catalog | TPL-*, SA6-* | agents | P/A | 9 | Must |
| Instructions hierarchy | INS-* | agents | P/A | 9 | Must |
| Knowledge scopes | KB-*, SA8-*, AG7-* | knowledge | P/A/C/R | 9 | Must |
| Number inventory/reserve | TEL-*, Q-002, SA9-*, AG4-* | telephony | P/A | 10 | Must |
| DID resolve + admission | CALL-001, voice rule | voice_runtime | R | 11 | Must |
| Inbound/outbound calls | §2.1, SA14-*, AG5-*, CU3-* | calls | All/R | 11–12 | Must |
| Transfers queues/SIP | XFER-*, Q-008 | calls, voice | A/R | 12 | Must |
| Voicemail in/out | Q-013 | calls, recordings | A/R | 12 | Must |
| Recording plane | CALL-003–005, ADR-002 | recordings | All | 13 | Must |
| Tool gateway | INT-*, Q-009 | integrations | R | 14 | Must |
| Per-customer integrations | Q-010, AG8-*, CU7-* | integrations | A/C | 14 | Must |
| Signed webhooks | WH-*, SA15-*, AG9-* | webhooks | A/P | 14 | Must |
| Notifications in-app+email | NOT-*, SA16-*, AG14-* | notifications | All | 15 | Must |
| Audit + overrides | AUD-*, SA17-* | audit | P | 15 | Must |
| Platform settings | SA19-*, §22 | platform | P | 15 | Must |
| Dashboards/reports | SA1-*, AG1-*, CU1-*, RPT-* | reporting | All | 16 | Must |
| MFA privileged | RBAC-008, SEC-013 | identity | P/A | 17 | Should |
| Impersonation | SA3-006 | identity | P | 17 | Should |
| Call/cost export | SA14-004, CU3-004 | calls | P/C | 16 | Should |
| Feature flags | SA19-004 | platform | P | 15 | Should |

Deferred features from SRS §32 are intentionally absent.
