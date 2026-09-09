# Vokit — Open Architectural Questions

## Purpose

This document contains **only** decisions that must be clarified before finalizing the Vokit architecture, ERD, and major system flows.

If the answer cannot change tenancy, the ERD, a core business/financial flow, or an Application ↔ Pipecat/Asterisk/SIP Edge / major external contract, it does not belong here.

## Already decided (do not re-ask)


| Decision                                                                                                                                                                                                                 | Source                                      |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------- |
| New Application is **greenfield Django + MySQL**, built from scratch                                                                                                                                                     | Product direction                           |
| **No** old Vokit Application code will be copied, migrated, or reused (`vokit-old/application` is reference-only)                                                                                                        | Product direction                           |
| Keep **Pipecat, Asterisk, SIP Edge**; modify them only when the new architecture/contracts require it                                                                                                                    | Product direction                           |
| SRS v1.0 is the product source of truth                                                                                                                                                                                  | `docs/Vokit_V1_Agency_Platform_SRS_v1.0.md` |
| Hierarchical tenancy: Platform → Agency → Customer → Agent; a customer belongs to **exactly one** agency; Super Admin is the only cross-tenant access                                                                    | SRS §3                                      |
| Three portals: Super Admin, Agency, Customer                                                                                                                                                                             | SRS §1                                      |
| Customer pays **Vokit** directly; agency earns commission; 15-day per-entry hold; ledger is financial source of truth; agency wallet may go negative after reversing paid commission                                     | SRS §5, §10–11                              |
| Agent is **customer-owned**; templates clone into an independent agent (not a live shared dependency)                                                                                                                    | SRS §13, §23, TPL-002                       |
| Knowledge scopes: Global / Agency / Customer / Agent                                                                                                                                                                     | SRS §14                                     |
| Inbound **and** outbound agent calling are in V1 (campaigns/robodialing are not)                                                                                                                                         | SRS §2.1, §32                               |
| Native CRM/accounting connectors **and** n8n/Zapier/Make **and** signed webhooks are in V1                                                                                                                               | SRS §18                                     |
| Notifications: in-app **and** email                                                                                                                                                                                      | SRS NOT-001                                 |
| Existing telephony **wire** contracts stay unless a question below forces a change: Asterisk DID-resolve (`routable`), Edge WS μ-law `/sip/media`, Pipecat bootstrap/events/end/transfer, Django hangup/transfer to Edge | Existing Pipecat / Asterisk / SIP Edge      |


Old Vokit (internal admin, prepaid balance, `assigned_admin_id`, no customer portal) is historical context only. Where it conflicts with the SRS, **the SRS wins**.

---



# BLOCKING QUESTIONS

Must be answered before architecture and ERD.

---



## Q-001 — User ↔ Agency ↔ Customer membership

**Question:**
What is the exact membership model?

Define whether:

- one User identity (email) is unique platform-wide
- a user may belong to **multiple agencies**
- a user may belong to **multiple customers** (same agency or different agencies)
- a platform staff user (Super Admin / Finance / Support) may **also** be an agency or customer user
- login is a single session with a chosen tenant context, or separate credentials per tenant

**Why this matters:**
SRS says platform, agency, and customer roles are distinct namespaces and that a user may hold multiple roles “only where explicitly supported” — it does not define membership cardinality. This is the User/Membership/Role ERD and every authorization check.

**Affected areas:**
Tenancy, ERD, authentication, RBAC, invitations, audit actor identity

**Current SRS/context:**
SRS §4, §20, §23. Customer belongs to one agency (TEN-002). No statement that a person can or cannot span agencies.

**Possible options:**

- A — Email unique globally; a user has at most one tenant membership (platform **or** one agency **or** one customer).
- B — Email unique globally; many memberships; user picks context at login.
- C — Credentials are not globally unique (same email can exist separately per tenant).
- D — Platform staff accounts cannot be tenant users (and vice versa), plus A or B for tenants.

**Status:** Decided

**Answer:**
A user can belong to only one tenant. The tenant can be either an Agency or a Customer. A single user cannot belong to multiple agencies or customers simultaneously.

Platform-level users such as Super Admin, Finance, and Support are separate platform users and are not members of any Agency or Customer tenant.

No tenant switching is required after login.

---



## Q-002 — Phone number ownership and who pays

**Question:**
Who **owns** a number in the data model, and who is invoiced for purchase/recurring number cost?

SRS lists PhoneNumber owner as Platform / Agency / Customer. Agency can search/buy; customer purchase is “no by default.” Recurring cost is for profitability reporting. The payer and the assignment chain are not specified.

Please define:

- inventory owner (platform pool vs agency-owned vs customer-owned)
- who Vokit invoices for number fees
- whether an agency may reassign a number between its customers
- whether one agent may have multiple numbers (one number → one routing target is already required)

**Why this matters:**
Changes PhoneNumber FKs, invoice line types, commissionability of number fees, and DID authorization.

**Affected areas:**
ERD, billing, telephony inventory, authorization

**Current SRS/context:**
TEL-001–004, SA9, AG4, Appendix A (customer cannot purchase by default), §23 PhoneNumber.

**Possible options:**

- A — Platform inventory; assigned Agency → Customer → Agent; **customer** is invoiced for number rent.
- B — Agency owns numbers and is invoiced; allocates to customers.
- C — Customer owns numbers; agency purchases on the customer’s behalf; **customer** is invoiced.

**Status:** Decided

**Answer:**
Phone numbers are owned by the Vokit Platform and managed through a central phone-number inventory controlled by Super Admin.

Agencies can select/reserve/assign available numbers for their agents. Once an Agency reserves a number for an Agent, that number becomes reserved for 10 minutes and cannot be purchased/reserved by another Agency during that reservation period.

The Customer associated with the Agent to whom the number is ultimately assigned will be billed for that phone number.

Rules:

- Platform owns the inventory.
- Agency performs the reservation/assignment process.
- Reservation duration = 10 minutes.
- During the reservation window, the number cannot be acquired by another Agency.
- The Customer is responsible for the number cost once it is assigned to their Agent.

---



## Q-003 — Customer usage: minutes vs money, and exhaustion behavior

**Question:**
What is the customer commercial source of truth for **usage**, and what happens when entitlement runs out **before** and **during** a call?

SA3-003 says “minute/monetary balance.” Plans have price, included minutes, top-ups, and overage **or** hard stop. §28 says do not abruptly terminate a call when minutes run out unless policy requires it. These need one rule.

Please define:

1. **What is stored and deducted?** Included/top-up **minutes** (money lives only on invoices), a **prepaid money wallet** (old-Vokit style), or both — and if both, drain order.
2. **Pre-answer admission** (Django DID-resolve `routable`): require remaining minutes, overage enabled, unpaid invoice rules, or something else?
3. **Mid-call zero minutes:** hang up, continue on overage, or grace then hang up? Is that **per plan** (PLAN-004) with a shipped default?

Chargeback/ban still immediately disables agents (SRS risk module). That is not in dispute.

**Why this matters:**
This is the customer ledger ERD, invoice line items, DID-resolve, and Pipecat heartbeat `continue_call`. Answering “minutes vs money” differently produces a different billing engine.

**Affected areas:**
ERD, billing, DID-resolve, Pipecat ↔ Django session contract, customer portal usage

**Current SRS/context:**
§10 plans/invoices/payments; PLAN-002–004; SA3-003; CALL-002; §28 out-of-minutes; old Vokit (reference only) hung up at `balance = 0`.

**Possible options:**

- A — Entitlements are minutes (included → top-up → overage if the plan allows). Money is invoices/payments only. Admission and mid-call follow the plan’s hard-stop vs overage flag.
- B — Prepaid monetary wallet plus subscription; specify drain order and admission (`balance > 0` vs minutes).
- C — Minutes-only packs, no subscription wallet; specify exhaustion.

**Status:** Decided

**Answer:**
Keep the overage behavior already defined by the SRS. The SRS remains the source of truth for how overage is calculated and charged. This decision does not replace or redefine those overage rules.

A grace period will exist when the customer's available minutes are exhausted:

- If overage is enabled according to the customer's Plan, continue using the SRS-defined overage behavior.
- If overage is disabled, the call may continue during the configured grace period after the available minutes are exhausted.
- Once the grace period expires, the call must end.

The new decision only adds grace-period behavior for the hard-stop case.

---

## Q-004 — Do agencies have their own Vokit plan/subscription?

**Question:**
SA11-003 says plans may be assigned to “customers/agencies as permitted.” The glossary and financial examples treat **Customer** as the subscriber (MRR, invoices, minutes).

Does an Agency also subscribe to a **platform plan** (limits, fees), or are plans **only** for customers, with agencies merely seeing which catalog they may assign?

**Why this matters:**
A second subscriber type doubles Subscription/Invoice ownership and entitlement checks. If agencies have no plan, agency limits are capability flags only (already in SRS).

**Affected areas:**
ERD, billing, entitlements, Super Admin plan assignment

**Current SRS/context:**
§23 Plan = platform, Subscription = customer. Agency row has commission_rate, not a plan. SA11-003 wording vs AG10-001 (agency views plans for assignment/sale).

**Possible options:**

- A — Plans attach only to Customers. “Assign to agencies” means which catalog an agency may sell.
- B — Agencies also have a platform subscription/plan, separate from their customers.

**Status:** Decided

**Answer:**
Plans attach only to Customers. Agencies do not have their own Vokit platform subscription/plan. 

---



## Q-005 — Currency boundary

**Question:**
Multi-currency **settlement/FX is deferred**. Agency creation still captures a currency.

Must all customers of an agency use **that same currency**? Is V1 a **single platform currency** (e.g. USD only)?

Commission is a percentage of customer payments. Mixed currencies without FX are undefined.

**Why this matters:**
Currency on Agency, Customer, Plan, Invoice, CommissionEntry, and Wallet. Mixing without FX breaks the ledger.

**Affected areas:**
ERD, billing, commission, payouts

**Current SRS/context:**
SA2-001 agency currency; SA19-001 currencies “subject to V1 scope”; §2.2 / §32 defer FX and multi-currency wallet settlement.

**Possible options:**

- A — One platform billing currency in V1.
- B — One currency per agency; all that agency’s customers, invoices, commissions, and payouts use it.
- C — Customer currency may differ (requires an FX/settlement rule — conflicts with deferred FX unless you define one).

**Status:** Decided

**Answer:**
V1 will support USD only.

All platform billing/financial operations in V1 will use USD:

- Agencies
- Customers
- Plans
- Subscriptions
- Invoices
- Payments
- Commissions
- Wallet/ledger
- Payout-related financial records

No other currencies will be supported in V1. Support for additional currencies may be introduced in a future version. Do not introduce FX or multi-currency settlement architecture into V1.

---



## Q-006 — Moving or closing customers and agencies

**Question:**
Two related ownership-lifecycle gaps:

1. **Reassignment:** AUD-005 lists customer reassignment as an audit event, but §3 says a customer has exactly one agency. Can Super Admin move a customer (and agents/numbers) from Agency A to Agency B? What happens to historical invoices, commissions, and calls (`agency_id` frozen vs updated)?
2. **Agency Closed:** §24.1 says existing services are “terminated/migrated per closure process” — process undefined. Must customers be migrated or terminated **before** Close is allowed?

**Why this matters:**
Determines whether `agency_id` on financial and call rows is immutable, and whether Close is a hard FK/lifecycle constraint.

**Affected areas:**
ERD, authorization, reporting, telephony (active DIDs), commission history

**Current SRS/context:**
TEN-002 store customer **and** agency on customer-owned objects. BR-014: **suspend** does not auto-kill existing customer service. Closed is a different state with no procedure.

**Possible options:**

- A — No reassignment in V1; Close requires Super Admin to terminate or migrate every customer first.
- B — Reassignment allowed; live resources move; **financial history keeps original agency_id**; future commission goes to the new agency. Close still requires empty-or-migrated customers.
- C — Case-by-case Super Admin only; no productized move; Close is a flag plus runbook.

**Status:** Decided

**Answer:**
Super Admin can reassign/migrate a Customer to another Agency.

- Historical invoices, billing records, and commission records remain with the original Agency context.
- Future records use the new Agency relationship.

Before closing an Agency, migrating its Customers/data to another Agency is **optional, not mandatory**. The Agency may be closed without requiring migration first.

---



## Q-007 — Portal delivery: server-rendered vs SPA

**Question:**
The SRS requires three web portals and does not specify UI technology. Copied Cursor rules still say Django Templates (old product).

For V1 Super Admin, Agency, and Customer portals, is the Application:

- Django Templates (HTML + session) for all three
- API-first Django + SPA (React/Vue/other)
- Hybrid (e.g. Templates for Super Admin, SPA for Agency/Customer)

This is **not** a question about CSS frameworks, component libraries, or folder layout.

**Why this matters:**
Determines whether Django’s primary external contract is HTML+forms or a versioned JSON API consumed by a separate frontend (auth, CSRF vs tokens, deployment of static apps).

**Affected areas:**
Application architecture, API surface, authentication, deployment of UI

**Current SRS/context:**
NFR-009 responsive agency/customer portals. White-label custom domains deferred. §30.1 REST-or-equivalent for APIs (telephony/webhooks still need JSON regardless).

**Possible options:**

- A — Django Templates for all three portals.
- B — SPA for all three; Django is the API/backend.
- C — Hybrid (specify which portals).

**Status:** Decided

**Answer:**
V1 frontend will use **React**. Django will provide the backend/API layer.

---



## Q-008 — Transfer destinations vs current SIP Edge

**Question:**
XFER-001 requires destinations such as phone number, department, queue, or supported SIP/client. Current SIP Edge transfer is **attended consult + REFER to an E.164**. There is no queue or SIP-client transfer API.

For V1, are production transfers **E.164 only** (department = a named number), or must we add queue/SIP-client behavior (almost certainly Asterisk and/or SIP Edge changes)?

Whisper/summary to the human (XFER-006 Should) and DTMF (AG6-003 Should) are out of this question unless you require them in V1.

**Why this matters:**
This is the only likely **SIP Edge / Asterisk contract expansion** besides outbound AI (already in SRS scope). Answering “queues in V1” redesigns the transfer flow.

**Affected areas:**
SIP Edge, Asterisk, Django transfer model, Pipecat `request_call_transfer`

**Current SRS/context:**
XFER-001 Must. Edge `POST /v1/calls/:id/transfer` `{ to }`. Keep Edge unchanged unless required.

**Possible options:**

- A — V1 E.164 only; “department” is a labeled number. No PBX queue.
- B — Django may hunt multiple E.164s using the existing Edge transfer API (no Edge rewrite).
- C — Real queues / SIP clients in V1 (approve Edge/Asterisk work).

**Status:** Decided

**Answer:**
V1 will support the SRS requirements for **queues and SIP clients**. Implement the architecture according to the SRS; do not simplify transfers to E.164-only transfers.

Keep existing Asterisk/SIP Edge contracts unless implementation of the SRS genuinely requires a change.

---



## Q-009 — Who executes in-call agent actions

**Question:**
During a live call the agent may run Vokit actions (`create_lead`, `invoke_webhook`, etc.). Today Pipecat’s only inbound tool is `request_call_transfer`, which calls **Django**.

Must Pipecat call **Django** as the tool/integration gateway (Django holds OAuth/webhook secrets, executes, returns a sanitized result), or would Pipecat call third parties directly?

1. WH-007 already requires a **synchronous** tool webhook with a strict timeout — that is a requirement, not a question. This question is **who** holds credentials and performs the I/O.

**Why this matters:**
Application ↔ Pipecat tool contract, secret isolation (AGT-006), and whether Pipecat becomes an integration runtime.

**Affected areas:**
Pipecat, Django, integrations, call action log, latency

**Current SRS/context:**
§18.2 normalized Vokit actions. INT-006 never speak secrets. Pipecat must not be assumed to store tenant OAuth tokens.

**Possible options:**

- A — Pipecat → Django tool gateway → CRM/webhook; Pipecat never holds tenant refresh tokens.
- B — Pipecat calls integrations directly (tokens in bootstrap).

**Status:** Decided

**Answer:**
Pipecat will call Django as the tool/integration gateway.

Flow:

```text
Pipecat
  → Django
  → CRM / webhook / external integration
```

Pipecat should not directly hold or use tenant OAuth credentials for these integrations.

---



## Q-010 — Integration connection sharing inside an agency

**Question:**
INT-001: connections belong to **agency or customer** and cannot be reused across **unauthorized** tenants.

May one **agency-owned** HubSpot/Salesforce/webhook connection be attached to **many customers** of that agency, or is a connection exclusive to a single owner (one agency record **xor** one customer record) with no sharing?

**Why this matters:**
`IntegrationConnection.owner` cardinality, OAuth install count, and whether agent actions may use a parent agency credential.

**Affected areas:**
ERD, authorization, secrets, agent tools

**Current SRS/context:**
INT-001. CU7-002 customer self-connect only if the agency enables it.

**Possible options:**

- A — Exclusive owner: agency **or** customer; no reuse across customers.
- B — Agency connections may be used by that agency’s customers; customer-owned connections stay customer-only.
- C — Split by type (e.g. CRM = customer, automation webhook = agency).

**Status:** Decided

**Answer:**
Every Customer will have its own integration connection.

An Agency-owned integration connection must NOT be shared across multiple Customers. Customer integrations are isolated per Customer.

Therefore:

- Customer A → its own HubSpot/Salesforce/etc. connection
- Customer B → its own connection
- Customer A cannot use Customer B's connection
- Agency-level connection sharing across Customers is not allowed in V1

Do not introduce shared agency credentials between Customers.

---



# IMPORTANT QUESTIONS

Should be answered before detailed architecture. Initial ERD can start from BLOCKING answers if needed.

---



## Q-011 — Payment processor

**Question:**
The billing chapter says “configured payment processor.” The risk/chargeback chapter is written around **Stripe** (Radar flags, dispute webhooks).

Confirm the V1 processor. If it is not Stripe, the inbound payment-risk architecture changes.

Not asking for SDK version, Checkout vs Elements, or Tax product SKUs.

**Why this matters:**
Inbound webhook contract, customer `processor_id`, risk automation, PCI boundary.

**Affected areas:**
Payments, risk module, webhooks, Customer billing fields

**Current SRS/context:**
§10 generic processor; risk module names Stripe repeatedly. Automated **payout** rails to agencies are deferred (manual Super Admin payout remains).

**Possible options:**

- A — Stripe (cards, subscriptions/invoices, disputes). Vokit is merchant of record (no Connect payouts).
- B — Another processor (name it).

**Status:** Decided

**Answer:**
V1 will support both Stripe and Braintree as payment processors.

Do not assume Stripe is the only processor. The payment architecture must use a processor abstraction so that Stripe and Braintree can both be supported without changing the core billing domain.

Do not choose SDKs or implementation details yet.

---



## Q-012 — Commission eligible amount

**Question:**
Commission % applies to which money: invoice subtotal, amount captured, amount captured minus processor fees, minus discounts? §10.4 already excludes tax (default), promo credits, and (default) pass-through fees; examples use $100 → 30% = $30 with no fee deduction.

**Why this matters:**
`CommissionEntry.eligible_base` meaning and platform-vs-agency reporting. Does not add entities if Q-003 is settled, but it does lock the financial engine.

**Affected areas:**
Commission ledger, reporting

**Current SRS/context:**
§10.4, BR-003, WAL-003 snapshot, Appendix C Example 1.

**Possible options:**

- A — Captured cash excluding tax; **ignore** processor fees (matches the $100 example).
- B — Captured cash excluding tax **and** processor fees.
- C — Per line-item `commissionable` flag only (plus §10.4 defaults).

**Status:** Decided

**Answer:**
Commission is calculated using the captured cash amount excluding tax, while processor fees are ignored for commission calculation.

---



## Q-013 — After-hours / voicemail

**Question:**
Agent builder lists business hours, voicemail, and fallback. Current Asterisk/Pipecat/Edge have **no voicemail mailbox**.

For V1 after-hours inbound: play a TTS message and hang up, transfer to an E.164, reject at DID-resolve (`outside_hours`), or a real voicemail inbox (recording + notification)?

**Why this matters:**
Real voicemail is a new artifact/flow (storage, retrieval, notifications). Message/transfer/reject can use existing call and transfer paths.

**Affected areas:**
Call flow, DID-resolve, storage, notifications, Agent config

**Current SRS/context:**
§12.2 Call Handling. XFER-004 time-dependent transfers. No voicemail component in existing telephony.

**Possible options:**

- A — No mailbox: TTS and/or transfer / DID reject only.
- B — Full voicemail in V1.

**Status:** Decided

**Answer:**
V1 will support **voicemail for both inbound and outbound calls**.

- **Outbound:** If the agent calls a number and the destination reaches voicemail, the agent should be able to leave a voicemail message.
- **Inbound:** If a caller reaches us after business hours, or the agent is unavailable for any other reason, the caller should be able to leave a voicemail message.

Voicemail must therefore be treated as a proper V1 capability for both call directions.

---



## Q-014 — Legacy production data

**Question:**
Will any **data** from old Vokit (customers, DIDs, call history, users) be imported into the new platform?

Application **code** will not be reused. This is only about data cutover. If yes, `assigned_admin` has no Agency — a mapping rule is required.

**Why this matters:**
A migration mapping is a one-time architecture/runbook; empty start is not.

**Affected areas:**
Cutover, Agency bootstrap, phone inventory

**Current SRS/context:**
SRS does not mention legacy migration.

**Possible options:**

- A — No migration; start empty (ops re-enter DIDs).
- B — Import inventory/call history only; commercial records start fresh.
- C — Full commercial migration with an explicit admin→agency mapping.

**Status:** Decided

**Answer:**
No old Vokit production data will be migrated. V1 starts with a clean/new database.

---



# Deferred Decisions

These do **not** block architecture. They will be decided during detailed design or implementation.

- Django package choices (DRF vs alternatives, celery vs other workers, cache library)
- Exact folder structure, naming conventions, serializer layout
- Primary key style (UUID vs bigint), indexes, MySQL charset
- Exact API path names, pagination, error JSON envelope
- Queue/broker product and configuration
- Email vendor, logging/monitoring/APM products
- Object-storage vendor and bucket layout (recordings/KYC/proofs clearly need file storage; provider is later)
- Docker/CI/CD, backup RPO/RTO, availability SLO numbers
- Qdrant hosting details (existing Pipecat knowledge path stays: Django writes, Pipecat retrieves, payload isolation; extend `group_id` for agency/agent)
- SIP Edge HTTP auth vs private-network-only (keep current unless security review requires an approved Edge change)
- Whether to reintroduce a Django `/sip/media` rollback peer (Pipecat is the media peer)
- `SIP_NODE_EVENTS_URL` (unused; ignore unless a later design needs Edge lifecycle events)
- Agent type enum vs template label, publish versioning/rollback depth, skip-LLM on knowledge hits
- Knowledge ingest details (file types, URL crawl, malware scan)
- Recording as paid add-on (PRIV-003 note) — plan entitlement flag, not a new bounded context
- Hold clock calendar vs business days; dunning retry days; min/max payout amounts
- KYC vendor (manual review is V1; automation deferred in SRS)
- Card-image OCR vs manual masking review
- Permanently-banned customer matching keys (need a fraud-index; exact keys are legal/design)
- Webhook HMAC details and per-event payload fields
- n8n hosting vs customer-hosted automation (generic signed webhooks satisfy AG8-002 unless a later decision says otherwise)
- Feature-flag product, second-approver workflows, impersonation
- Peak concurrent-call capacity and Pipecat replica count
- Detailed UI/UX, WCAG implementation, copy
- Cursor `architecture-rules.mdc` rewrite (after these answers + architecture docs)

---



# Remaining OPEN (awaiting product confirmation)

None. Q-001 through Q-014 are decided.