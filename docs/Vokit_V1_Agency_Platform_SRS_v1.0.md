VOKIT — Software Requirements Specification 

# **VOKIT** 

## **Software Requirements Specification** 

Version 1.0 — Agency-First AI Voice Platform 

|**Document Control**|**Value**|
|---|---|
|Product|Vokit|
|Release|V1 — Agency Edition|
|Document Type|Software Requirements Specification (SRS)|
|Version|1.0|
|Status|Baseline for Product, UX, Engineering and QA|
|Date|September 2026|
|Audience|Product, Engineering, QA, Operations, Finance, Compliance, Support|
|Confidentiality|Internal / Confidential|



_Purpose: define the complete functional, workflow, data, security, financial, operational, and non-functional requirements for the first production release of Vokit as an agency-centric AI voice-agent platform._ 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 1 

VOKIT — Software Requirements Specification 

### **Document Governance** 

|**Item**|**Rule**|
|---|---|
|Requirement language|“Shall” indicates a mandatory V1 requirement. “Should” indicates a recommended requirement. “May”<br>indicates an optional capability.|
|Change control|Changes affecting billing, commission, KYC, payouts, tenancy, permissions, call routing, or customer data<br>require documented product approval and regression testing.|
|Conflict rule|Where UI copy conflicts with this SRS, the business rules and state machines defined in this SRS take<br>precedence.|
|Compliance note|KYC, identity, payout, telephony, recording, messaging, privacy, tax and data-retention requirements vary by<br>jurisdiction. Vokit shall make compliance rules configurable and obtain legal/compliance review before enabling<br>a jurisdiction.|



### **Table of Contents** 

1. Executive Summary 

2. Product Scope and Release Boundaries 

3. Product Architecture and Tenancy 

4. Actors, Roles and Permission Model 

5. Core Business Rules 

6. End-to-End Onboarding and KYC 

7. Super Admin Portal 

###### 8. Agency Portal 

9. Customer Portal 

10. Customer, Subscription and Billing Engine 

11. Commission, Wallet and Payout Engine 

12. AI Agent Management and Agent Builder 

13. Agent Templates and Catalog 

14. Instructions, Knowledge and Training 

15. Phone Numbers and Telephony 

16. Calls, Recordings, Transcripts and Analytics 

17. Transfers and Human Handoff 

18. Integrations, Automations and Webhooks 

19. Notifications 

20. Users, Teams, Roles and Permissions 

21. Audit Logs and Administrative Overrides 

22. Platform Settings 

23. Data Model and Entity Ownership 

24. State Machines and Workflow Rules 

25. Security Requirements 

26. Privacy, Data Retention and Compliance Controls 

27. Non-Functional Requirements 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 2 

VOKIT — Software Requirements Specification 

28. Error Handling and Edge Cases 

29. Reporting and Metrics 

30. API and Webhook Requirements 

31. Acceptance Criteria and Release Gates 

32. Deferred / Post-V1 Scope Appendix A — Permission Matrix Appendix B — Event Catalog Appendix C — Financial Examples Appendix D — Glossary 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 3 

VOKIT — Software Requirements Specification 

### **1. Executive Summary** 

Vokit V1 is a multi-tenant AI voice-agent platform designed primarily for agencies that create, configure, sell, and manage AI phone agents for their own customers. Vokit remains the platform operator, billing party, telephony/AI service orchestrator, and final administrative authority. 

The release contains three primary application surfaces: (1) Vokit Super Admin Portal, (2) Agency Portal, and (3) Customer Portal. A customer belongs to one agency. Agencies earn a Super-Admin-defined commission on eligible customer revenue paid directly to Vokit. Every earned commission is placed on an independent 15-day hold before it becomes withdrawable. Agencies request payouts from available wallet balance; Vokit processes payouts in 1–2 business days, records private proof, and generates an agency-visible payout receipt. 

- KYC is mandatory for every agency before payout eligibility and may also gate operating capabilities according to platform policy. 

- Super Admin has platform-wide override authority, with every sensitive override recorded in immutable audit logs. 

- Agency customers receive a dedicated portal to monitor agents and calls, manage invoices/payment methods, purchase or add minutes, access usage, and manage permitted resources. 

- Agencies may purchase phone numbers, create multiple categories of AI agents, attach knowledge, configure transfers, and connect external systems through native integrations, n8n, Zapier, Make and signed webhooks. 

- V1 shall prioritize reliable multi-tenancy, billing/ledger integrity, KYC, payouts, telephony, agent management, integrations and customer monitoring over advanced marketplace/self-service creator economics. 

### **2. Product Scope and Release Boundaries** 

##### **2.1 In Scope** 

- Agency onboarding, KYC submission/review and activation. 

- Super Admin-created agency account and commission setup. 

- Agency, customer and platform user management. 

- Customer-direct billing to Vokit. 

- Plans, included minutes, top-ups/additional minutes and balances. 

- Commission calculation, 15-day holds, wallet ledger and payout requests. 

- Private payout proof plus generated agency receipt. 

- AI voice-agent creation, configuration, testing, assignment and lifecycle management. 

- Phone-number search/purchase/assignment/release through configured telephony provider(s). 

- Inbound and outbound agent call support where enabled by agent configuration and provider policy. 

- Call logs, recordings, transcripts, summaries and usage records subject to configuration and jurisdiction. 

- Transfers/human handoff. 

- Knowledge bases, instructions and reusable agent templates. 

- Integrations and automations using n8n, Zapier, Make, HubSpot, Salesforce, Zoho, QuickBooks and generic webhooks/API connectors. 

- Customer portal for monitoring, invoices, payments, minutes, agents and calls. 

- Notifications, audit logs, roles, permissions, app settings and operational dashboards. 

##### **2.2 Explicitly Deferred from V1** 

- Open public marketplace with third-party template seller payouts. 

- Fully autonomous agency white-label domain/theme reseller infrastructure unless separately approved. 

- Complex tax engine spanning all jurisdictions. 

- Multi-currency wallet settlement and FX trading. 

- Native mobile applications. 

- Carrier-of-record functionality. 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 4 

VOKIT — Software Requirements Specification 

- 

- 

   - Advanced predictive outbound campaigns, bulk robodialing or mass marketing automation. 

   - Custom self-hosted LLM/GPU orchestration as a customer-facing feature. 

- Revenue recognition/accounting system intended to replace professional accounting software. 

### **3. Product Architecture and Tenancy** 

The platform shall implement strict hierarchical tenancy. All business objects must be scoped to the correct owner. Crosstenant access is prohibited except for authorized Super Admin roles. 

|**Level**|**Ownership / Scope**|**Examples**|
|---|---|---|
|Platform|Owned by Vokit|Global plans, currencies, providers, global instructions, global knowledge,<br>admin users, template catalog|
|Agency|Owned by one agency|Agency settings, KYC, commission rate, wallet, payout methods, agency<br>users, agency knowledge, integrations|
|Customer|Owned by exactly one agency|Customer profile, subscription, invoices, balances, agents, numbers, calls,<br>customer users, knowledge|
|Agent|Normally belongs to one customer; may<br>originate from platform/agency template|Voice, instructions, tools, knowledge, number, transfer rules|
|Financial<br>Transaction|Linked to platform + agency + customer where<br>applicable|Payment, commission credit, hold release, adjustment, payout|



|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|TEN-001|Tenant isolation|All reads and writes shall enforce tenant scope server-side; UI filtering alone is<br>insufficient.|Must|
|TEN-002|Ownership chain|Customer-owned objects shall store customer and agency ownership to support<br>authorization, reporting and reconciliation.|Must|
|TEN-003|Super Admin access|Authorized Super Admin users may access all tenant data according to role<br>permissions.|Must|
|TEN-004|Agency boundary|Agency users shall never access another agency’s customers, calls, agents,<br>knowledge, wallet or payout data.|Must|
|TEN-005|Customer boundary|Customer users shall access only their assigned customer account and allowed<br>resources.|Must|
|TEN-006|Soft deletion|Financial, KYC and audit records shall not be hard-deleted through normal UI flows.|Must|



### **4. Actors, Roles and Permission Model** 

|**Actor**|**Primary Purpose**|**Default Authority**|
|---|---|---|
|Super Admin|Platform owner/operator|Full platform authority including overrides|
|Finance Admin|Billing, wallet and payout operations|Financial modules without unrestricted system configuration|
|Compliance/KYC<br>Reviewer|KYC and risk review|KYC documents/status and suspension recommendations|
|Support Admin|Customer/agency troubleshooting|Read access plus limited operational actions|
|Agency Owner|Runs agency account|Full agency scope except Super Admin-only rules|
|Agency Admin|Manages customers, agents, users and billing<br>visibility|Configurable agency permissions|
|Agency Agent Builder|Builds and maintains agents|Agent, knowledge, number and integration permissions as granted|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 5 

VOKIT — Software Requirements Specification 

|Agency Finance|Views commission/wallet and requests payouts|Financial permissions only|
|---|---|---|
|Customer<br>Owner/Admin|Manages customer account|Customer-level account, billing and permitted agent functions|
|Customer<br>Analyst/Viewer|Monitors calls and usage|Read-only or limited customer access|



Roles shall use granular RBAC. Platform roles and agency/customer roles are distinct permission namespaces. A user may hold multiple roles only where explicitly supported. 

### **5. Core Business Rules** 

|**Rule ID**|**Business Rule**|
|---|---|
|BR-001|Agency commission rate is established by Super Admin during agency creation or approval. Agency users cannot edit it.|
|BR-002|Customer payments are collected directly by Vokit through the configured payment processor.|
|BR-003|Eligible paid customer revenue creates agency commission according to the agency commission rate and commissionability<br>rules effective for that transaction.|
|BR-004|Each commission credit has its own 15-day hold measured from successful payment/settlement timestamp as defined by<br>payment policy.|
|BR-005|Held commission cannot be withdrawn. When the hold expires and no blocking event exists, it becomes Available.|
|BR-006|Only Available wallet balance can be included in a withdrawal request.|
|BR-007|Withdrawal requests are targeted for completion within 1–2 business days after acceptance for processing; this is an<br>operational SLA, not an unconditional guarantee where compliance/payment-provider holds apply.|
|BR-008|Super Admin may freeze, approve, reject, adjust, reverse or otherwise override eligible financial operations subject to audit<br>logging.|
|BR-009|Payout proof uploaded by Super Admin is private internal evidence and shall not be downloadable by the agency.|
|BR-010|Marking a payout Paid shall generate an agency-visible payout receipt containing non-sensitive payout metadata.|
|BR-011|KYC is mandatory for agency payout eligibility. Platform policy may also require KYC before customer creation, number<br>purchase or agent activation.|
|BR-012|Suspicious activity may move an agency to Restricted, Under Review or Suspended status.|
|BR-013|A suspended agency cannot create new customers. Super Admin controls whether other capabilities such as new agents,<br>number purchases, payouts or existing customer services remain available.|
|BR-014|Existing customer services shall not be automatically terminated solely because the agency is suspended unless Super Admin<br>or an automated safety rule explicitly disables them.|
|BR-015|All overrides, wallet adjustments, KYC status changes, payout actions, commission changes and suspensions shall be audit<br>logged.|
|BR-016|Customer MRR represents qualifying recurring customer subscription revenue. Expected Commission MRR shall be reported<br>separately to avoid conflating gross recurring revenue with agency earnings.|
|BR-017|Refunds, chargebacks and disputes can reverse or freeze associated commission according to transaction state.|
|BR-018|Commission rules must preserve the rate/rule snapshot used at transaction creation so later commission-rate changes do not<br>silently rewrite historical earnings.|
|BR-019|Customer portal permissions shall not allow unrestricted agent configuration unless the agency explicitly grants that capability.|
|BR-020|Platform-side financial values shall use immutable ledger entries; no feature may rely solely on a mutable wallet balance field<br>as source of truth.|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 6 

VOKIT — Software Requirements Specification 

### **6. End-to-End Onboarding and KYC** 

##### **6.1 Agency Creation Flow** 

1. Super Admin initiates Create Agency. 

2. Super Admin enters agency identity, owner/contact details, default status, commission rate, supported currency/region, and optional operating restrictions. 

3. System creates agency record in Invited / Onboarding status. 

4. System sends secure agency-owner invitation. 

5. Agency owner creates credentials, verifies email and accepts platform terms. 

6. Agency completes business profile and KYC application. 

7. Agency enters payout details; payout method remains unusable until verification rules are satisfied. 

8. KYC is submitted and enters Under Review. 

9. Authorized reviewer approves, rejects, or requests more information. 

10. When KYC and onboarding requirements are satisfied, agency enters Active status and receives portal access according to policy. 

##### **6.2 KYC Data Requirements** 

|**Category**|**Required Data / Evidence**|
|---|---|
|Business identity|Legal name, trading name, entity type, registration/incorporation number where applicable, incorporation country,<br>operating country, business address|
|Owner / controller|Full legal name, date of birth where lawful/required, nationality where lawful/required, residential address,<br>ownership/control relationship|
|Identity evidence|Government-issued identity document; supported types configured by jurisdiction|
|Business evidence|Registration/incorporation documentation, tax/business evidence where required|
|Address evidence|Recent acceptable proof of address where required|
|Payout evidence|Beneficiary name, account identifier, bank/provider details, country, currency; additional evidence when mismatch<br>occurs|
|Declarations|Accuracy declaration, beneficial ownership declaration where applicable, platform terms, acceptable use,<br>privacy/recording acknowledgements|



##### **6.3 KYC State Machine** 

|**State**|**Meaning**|**Allowed Next States**|
|---|---|---|
|Not Started|Agency has not begun KYC|Incomplete, Submitted|
|Incomplete|Application partially completed|Submitted|
|Submitted|Application locked/pending review|Under Review|
|Under Review|Reviewer is evaluating|More Information Required, Verified, Rejected|
|More Information<br>Required|Agency must correct/add evidence|Submitted|
|Verified|KYC passed|Expired, Suspended, Under Review|
|Rejected|KYC not accepted|Submitted if resubmission allowed|
|Expired|Previously verified evidence requires refresh|Submitted, Under Review|
|Suspended|KYC/risk access suspended|Under Review, Verified, Rejected|



**<mark>ID Requirement Detailed Requirement</mark>** 

**<mark>Priority</mark>** 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 7 

VOKIT — Software Requirements Specification 

|KYC-001|Mandatory KYC|System shall prevent payout request if agency KYC is not Verified.|Must|
|---|---|---|---|
|KYC-002|Document privacy|KYC files shall be restricted to authorized platform roles and excluded from<br>ordinary support/customer views.|Must|
|KYC-003|Review notes|Reviewer may add internal notes not visible to agency and external request notes<br>visible to agency.|Must|
|KYC-004|Reason codes|Rejections and information requests shall use structured reason codes plus<br>optional notes.|Must|
|KYC-005|Resubmission|Agency may replace or supplement requested evidence while preserving prior<br>version/audit history.|Must|
|KYC-006|Expiry|System shall support evidence/KYC expiration dates and re-verification.|Should|
|KYC-007|Risk override|Super Admin may freeze agency capabilities regardless of KYC status.|Must|
|KYC-008|KYC audit|Every view/download of highly sensitive KYC documents should be auditable where<br>technically feasible.|Should|



### **7. Super Admin Portal** 

The Super Admin Portal is the control plane for all Vokit tenants, commercial settings, financial operations, KYC, telephony inventory, agents, integrations, permissions and platform configuration. 

##### **7.1 Dashboard** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA1-001|Platform KPIs|Display total/active agencies, customers, agents, phone numbers, calls, minutes,<br>MRR, payments, commission liability, pending payouts and KYC queue.|Must|
|SA1-002|Financial summary|Display gross customer revenue, estimated platform share, agency commissions,<br>held commission, available commission and paid payouts for selected period.|Must|
|SA1-003|Operational health|Display failed calls, webhook failures, integration errors, low balances,<br>telephony/provider incidents and queue warnings where available.|Should|
|SA1-004|Drilldown|Dashboard cards shall link to filtered module views.|Must|
|SA1-005|Date filters|Support today, 7 days, 30 days, month-to-date and custom range.|Must|



##### **7.2 Agencies** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA2-001|Create agency|Create agency, owner invitation, commission, currency, status and initial<br>restrictions.|Must|
|SA2-002|Agency profile|View/edit legal/operating information subject to audit rules.|Must|
|SA2-003|Commission control|Set/change commission rate with effective date; historical commission entries<br>retain original snapshot.|Must|
|SA2-004|Status control|Activate, restrict, suspend, reactivate or close agency.|Must|
|SA2-005|Capability overrides|Enable/disable customer creation, agent creation, number purchase, payout<br>requests and other controlled capabilities.|Must|
|SA2-006|Financial overview|Show MRR, commission MRR, wallet states, payout history and customer revenue.|Must|
|SA2-007|Resources|View agency customers, agents, numbers, calls, integrations, team and knowledge.|Must|
|SA2-008|Internal notes|Maintain platform-only notes and risk flags.|Should|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 8 

VOKIT — Software Requirements Specification 

##### **7.3 Customers** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA3-001|Global customer directory|Search/filter all customers by agency, status, plan, balance and activity.|Must|
|SA3-002|Create customer|Super Admin may create a customer under any agency.|Must|
|SA3-003|Customer balance|View and adjust customer minute/monetary balance using ledger-backed<br>adjustments.|Must|
|SA3-004|Plan management|Assign/change plan, effective date and allowed overrides.|Must|
|SA3-005|Suspend customer|Suspend customer services independently of agency where authorized.|Must|
|SA3-006|Customer impersonation|If implemented, secure support impersonation must show persistent banner and<br>be fully audited.|Should|



##### **7.4 KYC Management** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA4-001|Review queue|Filter by status, age, country, agency and risk flags.|Must|
|SA4-002|Evidence review|Securely inspect submitted information and documents.|Must|
|SA4-003|Decision|Verify, reject or request additional information.|Must|
|SA4-004|Payout gating|KYC status shall feed payout eligibility automatically.|Must|
|SA4-005|Refresh|Trigger re-verification/expiry workflow.|Should|



##### **7.5 Agents** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA5-001|Global agent directory|List all agents across tenants with agency/customer/status/type/number.|Must|
|SA5-002|Create/manage|Super Admin can create, edit, pause, publish, clone or archive any agent.|Must|
|SA5-003|Diagnostics|Inspect runtime configuration, recent calls, errors and integrations.|Must|
|SA5-004|Override|Disable an agent immediately for abuse, billing or operational reasons.|Must|



##### **7.6 Agent Templates / Catalog** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA6-001|Template CRUD|Create/edit/version/archive reusable agent templates.|Must|
|SA6-002|Template metadata|Name, industry, use case, languages, default voice, instructions, recommended<br>tools, transfer rules.|Must|
|SA6-003|Visibility|Global, selected agencies or internal-only visibility.|Must|
|SA6-004|Install/clone|Agency can create an editable agent from allowed template.|Must|



##### **7.7 Instructions** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA7-001|Global instructions|Manage platform-level safety/behavior instructions applied to configured agents.|Must|
|SA7-002|Template instructions|Manage reusable template prompts/instructions.|Must|
|SA7-003|Precedence|Define deterministic inheritance/override precedence.|Must|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 9 

VOKIT — Software Requirements Specification 

SA7-004 

Versioning 

Record instruction revisions and publisher. 

|Should|
|---|



##### **7.8 Knowledge** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA8-001|Global knowledge|Create shared platform knowledge sources.|Must|
|SA8-002|Agency/customer access|Inspect tenant knowledge with authorization.|Must|
|SA8-003|Source management|Text, Q&A, file, URL and structured entries as supported.|Must|
|SA8-004|Processing state|Show uploaded, processing, ready, failed, stale.|Must|



##### **7.9 Phone Numbers** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA9-001|Inventory|Search and list platform-owned/tenant-assigned numbers.|Must|
|SA9-002|Purchase|Purchase supported numbers through configured provider.|Must|
|SA9-003|Assignment|Assign/reassign number to agency/customer/agent subject to rules.|Must|
|SA9-004|Release|Release numbers with confirmation and retention warnings.|Must|
|SA9-005|Cost visibility|Show recurring number cost and provider metadata to Super Admin.|Must|



##### **7.10 Transfers** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA10-001|Transfer directory|View tenant transfer destinations and rules.|Must|
|SA10-002|Override|Disable unsafe/invalid transfer targets.|Must|
|SA10-003|Diagnostics|View failed transfers and call outcomes.|Should|



##### **7.11 Plans** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA11-001|Plan CRUD|Create/version/archive plans.|Must|
|SA11-002|Entitlements|Price, billing cycle, included minutes, overage, agent/number/concurrency limits,<br>feature flags.|Must|
|SA11-003|Assignment|Assign to customers/agencies as permitted.|Must|
|SA11-004|Grandfathering|Existing subscriptions preserve plan version unless migrated.|Should|



##### **7.12 Billing & Payments** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA12-001|Payments|View customer payments, processor state and allocation.|Must|
|SA12-002|Invoices|View/generate/reconcile invoices.|Must|
|SA12-003|Refunds|Initiate/record refunds subject to permission and processor support.|Must|
|SA12-004|Disputes|Track disputes/chargebacks and associated commission impact.|Must|
|SA12-005|Manual adjustments|Create reasoned ledger adjustments; never silently mutate balances.|Must|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 10 

VOKIT — Software Requirements Specification 

##### **7.13 Wallet & Payouts** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA13-001|Agency wallet|Display pending/held/available/frozen/requested/paid values.|Must|
|SA13-002|Payout queue|Review requested payouts.|Must|
|SA13-003|Actions|Approve, reject, freeze, process, mark paid.|Must|
|SA13-004|Private proof|Upload private payout proof.|Must|
|SA13-005|Receipt|Generate agency-visible receipt on Paid.|Must|
|SA13-006|Adjustment|Create audited wallet debit/credit with reason and authorization.|Must|



##### **7.14 Call Records** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA14-001|Global calls|Search all calls by agency/customer/agent/number/date/status/direction.|Must|
|SA14-002|Call detail|Show provider ID, timestamps, duration, billable units,<br>recording/transcript/summary and tool activity where enabled.|Must|
|SA14-003|Cost|Show provider/AI cost components to authorized admin roles.|Should|
|SA14-004|Export|Export filtered call metadata subject to permission.|Should|



##### **7.15 Integrations & Webhooks** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA15-001|Provider registry|Configure available integrations and credentials strategy.|Must|
|SA15-002|Connection visibility|Inspect tenant integration connection status without exposing secrets.|Must|
|SA15-003|Webhook logs|Inspect deliveries, payload metadata, status, retries and response codes.|Must|
|SA15-004|Disable connection|Admin may disable compromised integration.|Must|



##### **7.16 Notifications** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA16-001|Template management|Manage system email/in-app notification templates.|Must|
|SA16-002|Delivery logs|Inspect notification delivery status.|Should|
|SA16-003|Announcements|Send platform or agency-targeted announcements.|Should|



##### **7.17 Audit Logs** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA17-001|Search|Search by actor, action, entity, tenant, IP/time and severity.|Must|
|SA17-002|Immutability|No normal UI may edit/delete audit events.|Must|
|SA17-003|Sensitive fields|Avoid storing raw secrets or full sensitive documents in logs.|Must|



##### **7.18 Users / Roles / Permissions** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA18-001|Admin users|Invite/disable platform users.|Must|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 11 

|SA18-002|RBAC|VOKIT — Software Requiremen<br>Create roles and permission bundles.|ts Specification<br>Must|
|---|---|---|---|
|SA18-003|Sensitive permission<br>controls|KYC, payout, wallet adjustment, commission edit and impersonation permissions<br>must be explicit.|Must|



##### **7.19 App Settings** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|SA19-001|Currency|Configure supported/display/base currencies subject to V1 scope.|Must|
|SA19-002|Business days|Configure payout business-day calendar/holidays if used for SLA calculation.|Should|
|SA19-003|Provider settings|Configure telephony, AI, payment and email providers through secure server-side<br>settings.|Must|
|SA19-004|Feature flags|Enable/disable features globally or by agency.|Should|
|SA19-005|Compliance settings|Recording disclosure, retention, number countries and KYC gates shall be<br>configurable where applicable.|Should|



### **8. Agency Portal** 

The Agency Portal enables verified/authorized agencies to manage their business on Vokit while remaining isolated from other agencies. Modules and actions are permission- and status-gated. 

##### **8.1 Agency Dashboard** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG1-001|KPIs|Customers, active agents, numbers, calls, minutes, customer MRR, expected<br>commission MRR, commission earned, held, available, pending payout and lifetime<br>paid.|Must|
|AG1-002|Alerts|KYC, payment, low balance, failed integration, agent errors and payout statuses.|Must|
|AG1-003|Trends|Basic revenue/calls/minutes trends.|Should|



##### **8.2 Customers** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG2-001|Create customer|Create customer when agency is Active and customer-creation capability is<br>enabled.|Must|
|AG2-002|Invite customer users|Invite customer owner/admin users.|Must|
|AG2-003|Customer profile|Manage business/contact details and service status within allowed fields.|Must|
|AG2-004|Plan|Assign from agency-available plans or request/admin-controlled plan.|Must|
|AG2-005|Resources|View customer agents, numbers, calls, knowledge, integrations, invoices and<br>usage.|Must|



##### **8.3 Agents** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG3-001|Create agent|Create from scratch or allowed template.|Must|
|AG3-002|Configure|Voice, language, instructions, knowledge, tools, transfers, business hours, number<br>and behavior.|Must|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 12 

|||VOKIT — Software Requir|ements Specification|
|---|---|---|---|
|AG3-003|Test|Run browser/simulator tests before activation.|Must|
|AG3-004|Publish|Activate/deactivate agent subject to customer plan/balance/status.|Must|
|AG3-005|Clone|Clone within same agency/customer boundaries.|Should|



##### **8.4 Phone Numbers** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG4-001|Search/buy|Search available supported numbers and purchase when permitted.|Must|
|AG4-002|Assign|Assign to customer and compatible agent.|Must|
|AG4-003|Configure|Inbound routing, caller ID options where lawful/provider-supported, transfer and<br>fallback.|Must|
|AG4-004|Release|Release with explicit confirmation and impact warning.|Must|



##### **8.5 Calls** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG5-001|Call list|View agency-wide calls with filters.|Must|
|AG5-002|Call detail|Recording/transcript/summary/outcome/tools when enabled.|Must|
|AG5-003|Customer privacy|Agency access is subject to its customer agreement and platform policy.|Must|



##### **8.6 Transfers** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG6-001|Destinations|Create verified transfer destinations/teams.|Must|
|AG6-002|Rules|Business hours, fallback, no-answer and conditional transfer rules.|Must|
|AG6-003|DTMF|Configure extension/DTMF sequence where supported.|Should|



##### **8.7 Knowledge** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG7-001|Agency knowledge|Create reusable agency-wide sources.|Must|
|AG7-002|Customer knowledge|Manage customer-specific sources.|Must|
|AG7-003|Agent attachment|Attach/detach allowed sources to agents.|Must|
|AG7-004|Sync/reindex|Refresh supported URL/file sources.|Should|



##### **8.8 Integrations & Automations** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG8-001|Connections|Connect authorized providers such as HubSpot, Salesforce, Zoho, QuickBooks.|Must|
|AG8-002|Automation platforms|Connect or configure n8n, Zapier and Make through webhooks/API.|Must|
|AG8-003|Actions|Map agent actions to integrations.|Must|
|AG8-004|Test|Test connection/action and show errors.|Must|
|AG8-005|Secrets|Credentials/tokens shall not be displayed after storage.|Must|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 13 

VOKIT — Software Requirements Specification 

##### **8.9 Webhooks** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG9-001|Endpoint CRUD|Create/update/disable endpoints.|Must|
|AG9-002|Events|Subscribe to allowed event types.|Must|
|AG9-003|Signing secret|Generate/rotate signing secret.|Must|
|AG9-004|Delivery log|View status, response code, retry and timestamp.|Must|
|AG9-005|Test event|Send safe sample event.|Must|



##### **8.10 Plans & Customer Billing Visibility** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG10-001|Plan catalog|View plans available for assignment/sale.|Must|
|AG10-002|Customer invoices|View customer invoices and payment status.|Must|
|AG10-003|No payment diversion|Agency shall not change Vokit payment destination.|Must|
|AG10-004|Revenue view|Show commissionable revenue separately from gross customer billing.|Must|



##### **8.11 Wallet & Payouts** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG11-001|Wallet summary|Show held, available, frozen, pending withdrawal and lifetime paid.|Must|
|AG11-002|Ledger|Show every earning, reversal, adjustment, hold release and payout.|Must|
|AG11-003|Withdrawal|Request withdrawal from available balance only.|Must|
|AG11-004|Payout method|Manage approved payout details subject to KYC/risk reverification.|Must|
|AG11-005|Receipts|View/download generated payout receipts; private admin proof remains<br>inaccessible.|Must|



##### **8.12 KYC** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG12-001|Application|Complete KYC and upload required evidence.|Must|
|AG12-002|Status|View status and visible review notes.|Must|
|AG12-003|Resubmit|Provide requested information.|Must|
|AG12-004|Payout gate|Clearly show payout restriction until Verified.|Must|



##### **8.13 Team** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AG13-001|Invite|Invite agency team users.|Must|
|AG13-002|Roles|Assign allowed agency roles.|Must|
|AG13-003|Revoke|Disable user access.|Must|



##### **8.14 Notifications & Settings** 

**<mark>Requirement Detailed Requirement</mark>** 

**<mark>Priority</mark>** 

**<mark>ID</mark>** 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 14 

|||VOKIT — Software Require|ments Specification|
|---|---|---|---|
|AG14-001|Preferences|Configure agency-level notification preferences.|Must|
|AG14-002|Brand/profile|Manage allowed agency profile/branding fields.|Should|
|AG14-003|Security|Manage sessions/password/MFA when supported.|Must|



### **9. Customer Portal** 

The Customer Portal is a customer-facing web application under Vokit authentication. It enables an agency customer to monitor service and manage permitted commercial/operational tasks without exposing agency-only or platform-only data. 

##### **9.1 Dashboard** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|CU1-001|Overview|Show agents, calls this month, minutes used/remaining, plan, invoice status and<br>recent calls.|Must|
|CU1-002|Service alerts|Show low minutes, payment due, agent offline and important notifications.|Must|



##### **9.2 Agents** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|CU2-001|Monitor|View assigned agents, status, number and high-level configuration.|Must|
|CU2-002|Permissions|Editing capability is disabled by default and granted explicitly by agency/platform<br>policy.|Must|
|CU2-003|Limited actions|Allow pause/resume or selected editable fields only when permission exists.|Should|



##### **9.3 Calls** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|CU3-001|Call history|View customer calls only.|Must|
|CU3-002|Artifacts|View recording/transcript/summary if enabled and authorized.|Must|
|CU3-003|Filters|Filter by agent, number, date, direction, outcome.|Must|
|CU3-004|Export|Allow export where agency/customer permission permits.|Should|



##### **9.4 Usage & Minutes** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|CU4-001|Usage|Show included, consumed, remaining and additional minutes.|Must|
|CU4-002|Breakdown|Show usage by agent/date where feasible.|Must|
|CU4-003|Top-up|Purchase additional minute packages offered by Vokit.|Must|



##### **9.5 Invoices & Payments** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|CU5-001|Invoices|View open/paid/failed/refunded invoices.|Must|
|CU5-002|Pay|Pay outstanding invoices through Vokit.|Must|
|CU5-003|Payment methods|Add/update payment method through processor-hosted secure flow where|Must|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 15 

VOKIT — Software Requirements Specification 

|||possible.||
|---|---|---|---|
|CU5-004|Receipts|Download customer payment receipts/invoices.|Must|



##### **9.6 Knowledge** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|CU6-001|View|View customer knowledge attached to agents.|Must|
|CU6-002|Edit|Upload/edit knowledge only where agency grants permission.|Should|



##### **9.7 Integrations** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|CU7-001|View status|See integrations relevant to customer.|Must|
|CU7-002|Connect|Connect customer-owned accounts only where agency enables self-service.|Should|



##### **9.8 Team & Settings** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|CU8-001|Users|Invite/manage customer team subject to role.|Must|
|CU8-002|Notifications|Manage customer notification preferences.|Must|
|CU8-003|Profile|Manage allowed business/contact settings.|Must|



### **10. Customer, Subscription and Billing Engine** 

##### **10.1 Customer Account Model** 

|**Field Group**|**Examples**|
|---|---|
|Identity|Customer ID, agency ID, legal/display name, email, phone, country, timezone|
|Commercial|Plan, subscription status, billing cycle, included minutes, overage policy, currency|
|Service|Status, active agents, phone numbers, feature entitlements|
|Billing|Processor customer ID, invoice settings, tax fields where required, payment method state|
|Controls|Agency permissions, customer portal permissions, suspension reason/state|



##### **10.2 Plan Model** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|PLAN-001|Plan versioning|Each plan shall have immutable/versioned commercial terms once used by active<br>subscriptions.|Must|
|PLAN-002|Included minutes|Plan shall define included billable minutes/units per billing cycle.|Must|
|PLAN-003|Top-ups|Plan may permit additional minute packages.|Must|
|PLAN-004|Overage|Plan may define overage price/rules or hard stop.|Must|
|PLAN-005|Feature entitlements|Plan may limit number of agents, phone numbers, concurrency, recordings,<br>integrations and other capabilities.|Must|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 16 

VOKIT — Software Requirements Specification 

|PLAN-006|Billing cycle|Support at least monthly recurring billing for V1; other cycles configurable if<br>implemented.|Must|
|---|---|---|---|
|PLAN-007|Proration|If plan changes are supported mid-cycle, proration behavior must be deterministic<br>and shown before confirmation.|Should|



##### **10.3 Payment Flow** 

11. Invoice/subscription charge is created for customer. 

12. Payment processor attempts payment. 

13. On success, Vokit records payment transaction and invoice Paid state. 

14. System identifies commissionable line items and calculates agency commission using transaction snapshot. 

15. System creates commission ledger entry in On Hold state with available_at = qualifying payment timestamp + 15 days. 

16. Customer minute/subscription entitlements are activated or renewed. 

17. Customer and agency receive appropriate notification. 

18. Payment failure triggers retry/dunning or service rule according to configuration. 

##### **10.4 Commissionable Revenue Rules** 

|**Item**|**Default**<br>**Commissionability**|**Rule**|
|---|---|---|
|Subscription base fee|Yes|Commission on eligible net amount defined by policy|
|Minute top-up|Yes|Commission if sold as eligible Vokit service revenue|
|Paid add-on|Yes|If marked commissionable|
|Tax|No|Excluded by default|
|Refunded amount|No / reversed|Associated commission reversed proportionally|
|Chargeback/dispute|Frozen/reversed|Commission frozen or reversed according to state|
|Promotional credit|No|No cash revenue|
|Manual goodwill credit|No|Unless Super Admin explicitly marks commissionable|
|Pass-through<br>regulatory/carrier fee|Configurable, default No|Avoid commission unless business policy approves|



### **11. Commission, Wallet and Payout Engine** 

##### **11.1 Ledger Architecture** 

The wallet shall be ledger-based. A cached balance may be maintained for performance, but the authoritative balance must be reproducible from immutable financial entries. 

|**Ledger Entry Type**|**Effect**|**Example**|
|---|---|---|
|Commission Earned|Credit, initially held|+$30 from paid customer invoice|
|Hold Released|State transition / availability event|Commission becomes withdrawable|
|Commission Reversal|Debit|Refund/chargeback reverses prior earning|
|Manual Credit|Credit|Authorized adjustment|
|Manual Debit|Debit|Authorized correction|
|Payout Reserved|Moves available to withdrawal pending|-$500 available / +$500 pending payout|
|Payout Paid|Settles reserved liability|Payout completed|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 17 

VOKIT — Software Requirements Specification 

|Payout Rejected/Cancelled|Releases reserved amount|Returns amount to available if eligible|
|---|---|---|
|Freeze|State/availability constraint|Blocks specified funds|



##### **11.2 Wallet Balance Buckets** 

|**Bucket**|**Definition**|**Withdrawable**|
|---|---|---|
|Pending|Commission event created but not yet final/eligible for hold|No|
|On Hold|Valid commission within 15-day hold|No|
|Available|Hold elapsed and no freeze/reversal|Yes|
|Frozen|Funds blocked by risk/compliance/admin action|No|
|Withdrawal Pending|Funds reserved in an active payout request|No|
|Lifetime Paid|Historical aggregate of completed payouts|N/A|



|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|WAL-001|Per-entry hold|Every commission earning shall store its own earned_at and available_at<br>timestamps.|Must|
|WAL-002|No double spend|Payout request shall atomically reserve requested available funds.|Must|
|WAL-003|Snapshot|Commission percentage and eligible base amount shall be stored on the<br>commission transaction.|Must|
|WAL-004|Reconciliation|System shall reconcile payment, invoice, commission and payout references.|Must|
|WAL-005|Negative balances|If already-paid commission is reversed, system may create negative available<br>balance/receivable to be offset by future earnings according to policy.|Must|
|WAL-006|Freeze precedence|Frozen status shall override normal hold release and withdrawal availability.|Must|
|WAL-007|Admin adjustments|Manual adjustments require amount, direction, reason, actor and timestamp.|Must|



##### **11.3 Payout Flow** 

19. Agency opens Wallet > Withdraw. 

20. System validates KYC Verified, agency status, payout capability, payout method and available balance. 

21. Agency enters amount within configured limits and confirms. 

22. System atomically creates payout request and moves/reserves amount from Available to Withdrawal Pending. 

23. Super Admin/Finance reviews request and risk/compliance context. 

24. Request becomes Approved or Rejected/Frozen. 

25. On processing, status becomes Processing. 

26. After external transfer, Super Admin uploads private payout proof and enters non-sensitive transaction reference. 

27. Super Admin marks payout Paid. 

28. System finalizes ledger, generates receipt, records paid timestamp and notifies agency. 

29. Agency can view/download generated receipt but cannot access uploaded private proof. 

##### **11.4 Payout Receipt Fields** 

- Vokit payout receipt number 

- Agency legal/display name 

- Payout request ID 

- Amount and currency 

- Payout method label (masked as appropriate) 

- Request date 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 18 

VOKIT — Software Requirements Specification 

- Paid date 

- Status = Paid 

- Non-sensitive/masked transaction reference 

- Vokit issuer details required by business policy 

- Optional statement that receipt confirms payout processing and is not the underlying banking proof 

### **12. AI Agent Management and Agent Builder** 

##### **12.1 Agent Types** 

- AI Receptionist 

- Appointment Booking Agent 

- Customer Support Agent 

- Sales / Lead Qualification Agent 

- Real Estate Agent 

- Dental/Medical Receptionist subject to applicable compliance 

- Restaurant Reservation Agent 

- Hotel Receptionist 

- Order Status / E-commerce Agent 

- Dispatch / Service Agent 

- After-hours Answering Agent 

- FAQ / Information Agent 

- Custom Agent 

##### **12.2 Agent Builder Stages** 

|**Stage**|**Configuration**|
|---|---|
|Identity|Agent name, customer, use case/type, status, timezone|
|Voice & Language|Provider, voice, language, speaking style/speed if supported|
|Persona & Instructions|Role, goals, constraints, greeting, fallback behavior, global/agency/customer/agent instruction layering|
|Knowledge|Attached global/agency/customer/agent sources|
|Call Handling|Inbound/outbound permissions, business hours, voicemail/fallback, silence/timeouts, interruption settings|
|Tools / Actions|Allowed actions and parameter schema|
|Integrations|Connection/action mapping to CRM, automation or API|
|Transfers|Destinations, triggers, business hours, fallback|
|Phone Number|Assigned number and routing|
|Compliance|Recording disclosure, prohibited behavior, required disclaimers where configured|
|Test|Browser simulation/test call, transcript and tool traces|
|Publish|Preflight validation then activation|



|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AGT-001|Draft state|New agent begins Draft and cannot receive production traffic until required fields<br>pass validation.|Must|
|AGT-002|Publish validation|System validates customer status, plan entitlement, number/routing, instructions,<br>voice/provider and required compliance fields before publish.|Must|
|AGT-003|Pause|Agency/Super Admin can pause agent without deleting configuration.|Must|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 19 

VOKIT — Software Requirements Specification 

|AGT-004|Versioning|Published configuration changes should preserve revision history or at minimum<br>audit-level change history.|Should|
|---|---|---|---|
|AGT-005|Tool allowlist|Agent can invoke only explicitly configured tools/actions.|Must|
|AGT-006|Secret isolation|Integration credentials are never included in agent prompt or transcript.|Must|
|AGT-007|Knowledge isolation|Retrieval must respect tenant/customer/agent access scope.|Must|
|AGT-008|Fallback|Failures shall have configurable safe fallback behavior such as message, transfer<br>or hangup.|Must|



### **13. Agent Templates and Catalog** 

V1 shall use an Agent Templates / Catalog module rather than a full open marketplace. Templates are reusable starting configurations. A later Marketplace may add third-party publishing and economics. 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|TPL-001|Template creation|Super Admin creates templates; optional agency-private templates may be<br>supported.|Must|
|TPL-002|Clone semantics|Installing a template creates an independent editable agent configuration rather<br>than a live shared dependency unless version-locking is explicitly designed.|Must|
|TPL-003|Metadata|Industry, use case, description, supported language, required integrations, default<br>instructions and recommended knowledge checklist.|Must|
|TPL-004|Visibility|Platform can restrict templates to selected agencies.|Must|
|TPL-005|Version|Template revisions shall not silently alter existing deployed agents.|Must|



### **14. Instructions, Knowledge and Training** 

##### **14.1 Instruction Hierarchy** 

Instruction precedence shall be deterministic. Recommended order from highest policy authority to most specific contextual customization: Platform Safety/Global Mandatory Rules → Template/Base Instructions → Agency Instructions → Customer Instructions → Agent Instructions. Mandatory platform safety rules cannot be overridden by lower scopes. 

|**ID**|**Requirement**|**Detailed Requirem**|**ent**|**Priority**|
|---|---|---|---|---|
|INS-001|Global rules|Platform-level manda|tory rules apply where configured.|Must|
|INS-002|Tenant overrides|Agency/customer/age|nt layers can extend or override only permitted fields.|Must|
|INS-003|Resolved preview|Builder should show e|ffective/resolved instructions or clearly indicate inheritance.|Should|
|INS-004|Version history|Changes to productio|n instructions shall be audit logged.|Must|
|**14.2 Kno**<br>**Scope**|**wledge Hierarchy**<br>**Purpose**||**Examples**||
|Global|Platform-shared inform|ation|Generic policies, platform-controlled reference content||
|Agency|Reusable across agenc<br>allowed|y customers where|Agency service playbooks||
|Customer|Customer business kno|wledge|Hours, services, policies, FAQs||
|Agent|Agent-specific content||Campaign/role-specific Q&A or procedural data||



##### **14.2 Knowledge Hierarchy** 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 20 

VOKIT — Software Requirements Specification 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|KB-001|Source types|Support text/manual Q&A plus file/URL ingestion where configured.|Must|
|KB-002|Processing states|Queued, Processing, Ready, Failed, Stale/Needs Refresh.|Must|
|KB-003|Isolation|Retrieval shall never cross unauthorized tenant/customer scopes.|Must|
|KB-004|Delete semantics|Removing source from an agent detaches it; deleting underlying source requires<br>permission and impact warning.|Must|
|KB-005|Citation/debug metadata|Internal diagnostics should identify which source/chunk influenced a response<br>where provider architecture permits.|Should|



##### **14.3 Training / Academy** 

“Training” in V1 should be separated into two concepts: agent configuration/testing inside Agent Builder, and an Academy/Help Center for users. Academy topics should include onboarding, first agent, prompts/instructions, knowledge, phone numbers, transfers, integrations, billing, KYC and troubleshooting. 

### **15. Phone Numbers and Telephony** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|TEL-001|Provider abstraction|Phone-number and call operations shall use provider adapters so provider-specific<br>fields do not leak into core business logic unnecessarily.|Must|
|TEL-002|Search|Authorized user can search available numbers by supported<br>country/area/capability.|Must|
|TEL-003|Purchase|Purchase requires active tenant status, entitlement, payment/balance rules and<br>provider success.|Must|
|TEL-004|Assignment|A number can be assigned to one active routing target at a time unless provider<br>architecture explicitly supports otherwise.|Must|
|TEL-005|Inbound routing|Incoming calls route to assigned agent or configured fallback.|Must|
|TEL-006|Outbound caller ID|Outbound calls use authorized caller ID/number according to provider/jurisdiction<br>rules.|Must|
|TEL-007|Release|Release requires confirmation; system records release state and provider result.|Must|
|TEL-008|Recurring cost|System records provider number cost for profitability reporting.|Should|
|TEL-009|Provisioning state|Pending, Active, Failed, Releasing, Released.|Must|
|TEL-010|Failure reconciliation|Provider success with local failure or vice versa shall be detected/reconciled<br>through idempotent operations.|Must|



### **16. Calls, Recordings, Transcripts and Analytics** 

##### **16.1 Call Record Fields** 

|**Category**|**Fields**|
|---|---|
|Identifiers|Vokit call ID, provider call ID, agency ID, customer ID, agent ID, number ID|
|Call metadata|Direction, caller, callee, start/ringing/answer/end timestamps, status, disconnect reason|
|Usage|Duration, billable seconds/minutes, plan allocation, overage units|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 21 

VOKIT — Software Requirements Specification 

|AI|Model/provider identifiers where logged, voice/STT provider, latency metrics where available|
|---|---|
|Artifacts|Recording, transcript, summary, sentiment/outcome where enabled|
|Actions|Tools invoked, transfers, appointments/leads/actions created|
|Cost|Telephony/STT/TTS/LLM cost components visible only to authorized roles|



|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|CALL-001|Lifecycle|System records call states and terminal reason.|Must|
|CALL-002|Usage charging|Billable usage shall be calculated consistently and linked to customer<br>balance/subscription.|Must|
|CALL-003|Artifact permissions|Recording/transcript access shall respect customer/agency/platform permissions<br>and legal configuration.|Must|
|CALL-004|Recording disclosure|System shall support configurable disclosure/consent behavior; legal configuration<br>is jurisdiction-dependent.|Must|
|CALL-005|Retention|Recordings/transcripts shall have configurable retention and deletion controls.|Must|
|CALL-006|Search|Support date, agency, customer, agent, number, direction, status and outcome<br>filters.|Must|
|CALL-007|Export|Authorized exports must be tenant-scoped and auditable for sensitive data.|Should|



### **17. Transfers and Human Handoff** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|XFER-001|Destinations|Agency can create transfer destinations such as phone number, department,<br>queue or supported SIP/client target.|Must|
|XFER-002|Verification|External phone destinations should be verified or validated before production use.|Should|
|XFER-003|Triggers|Agent may transfer on user request, intent, confidence/error, emergency rule or<br>configured business logic.|Must|
|XFER-004|Business hours|Transfer rules may be time/day dependent.|Must|
|XFER-005|No-answer|Provide timeout and fallback behavior.|Must|
|XFER-006|Context|Where supported, preserve caller context and optionally provide whisper/summary<br>to recipient.|Should|
|XFER-007|Audit|Record transfer attempt/outcome in call record.|Must|



### **18. Integrations, Automations and Webhooks** 

##### **18.1 Supported Integration Categories** 

|**Category**|**V1 Targets / Pattern**|
|---|---|
|CRM|HubSpot, Salesforce, Zoho|
|Accounting|QuickBooks|
|Automation|n8n, Zapier, Make|
|Generic developer|Signed webhooks, REST API actions|
|Calendar / productivity|May be added via native connector or automation platform based on release capacity|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 22 

VOKIT — Software Requirements Specification 

##### **18.2 Agent Action Model** 

Agents should call normalized Vokit actions rather than reasoning directly about third-party APIs. Example actions: create_lead, create_contact, update_contact, book_appointment, lookup_customer, create_ticket, send_notification, check_order, create_invoice_context, transfer_call, invoke_webhook. 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|INT-001|Connection ownership|Integration connections belong to agency or customer and cannot be reused across<br>unauthorized tenants.|Must|
|INT-002|OAuth|Use provider OAuth where supported; refresh tokens stored encrypted/server-side.|Must|
|INT-003|Action schema|Each action defines name, description, input schema, output schema, timeout and<br>error behavior.|Must|
|INT-004|Permission|Only configured agent actions may execute.|Must|
|INT-005|Test mode|Builder provides safe connection/action test.|Must|
|INT-006|Failure behavior|Agent receives sanitized failure result; secrets/internal stack traces are never<br>spoken to caller.|Must|
|INT-007|Rate limits|Respect provider limits and surface recoverable errors.|Must|
|INT-008|Revocation|Disconnect invalidates credentials and disables dependent actions.|Must|



##### **18.3 Webhooks** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|WH-001|Event subscription|Endpoint subscribes to one or more allowed event types.|Must|
|WH-002|Signing|All outbound webhooks shall be signed using a rotatable tenant-specific secret.|Must|
|WH-003|Delivery ID|Each delivery has unique ID and event ID for idempotency.|Must|
|WH-004|Retry|Retry transient failures using bounded backoff; do not retry permanent validation<br>errors indefinitely.|Must|
|WH-005|Logs|Store endpoint, event, status code, attempt count, timestamp and sanitized<br>response metadata.|Must|
|WH-006|Replay|Authorized users may replay eligible failed deliveries.|Should|
|WH-007|Interactive agent webhook|Support synchronous tool/action webhook with strict timeout and schema<br>validation.|Must|
|WH-008|Knowledge webhook|Support controlled external knowledge lookup or knowledge synchronization<br>pattern with tenant validation.|Must|



### **19. Notifications** 

|**Trigger**|**Recipients / Channels**|
|---|---|
|Agency invitation|Agency owner email|
|KYC submitted/approved/rejected/more-info|Agency owner + compliance notifications|
|Customer invitation|Customer user email|
|Payment success/failure|Customer + agency visibility as configured|
|Low minutes|Customer and agency|
|Commission available|Agency finance/owner|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 23 

VOKIT — Software Requirements Specification 

|Payout requested|Agency + Vokit finance|
|---|---|
|Payout paid/rejected|Agency|
|Agency suspension/restriction|Agency owner/admin|
|Agent/number/integration failure|Agency operational users|
|Platform announcement|Selected users/tenants|



|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|NOT-001|Channels|Support in-app and email for V1; webhook events may supplement.|Must|
|NOT-002|Preferences|Users may disable non-mandatory notifications.|Must|
|NOT-003|Mandatory notices|Security, billing, KYC and suspension notices may be non-optional.|Must|
|NOT-004|Template variables|Templates shall use validated variables and escape untrusted content.|Must|
|NOT-005|Delivery log|Track delivery status where provider supports.|Should|



### **20. Users, Teams, Roles and Permissions** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|RBAC-001|Invite lifecycle|Invited, Active, Suspended/Disabled states.|Must|
|RBAC-002|Least privilege|Default roles grant only necessary permissions.|Must|
|RBAC-003|Financial separation|Payout approval, wallet adjustment and commission modification shall be<br>separate explicit permissions.|Must|
|RBAC-004|KYC access|KYC document access shall be restricted to designated platform roles.|Must|
|RBAC-005|Team scope|Agency role assignments cannot grant platform-level permissions.|Must|
|RBAC-006|Customer role scope|Customer roles cannot grant agency-level permissions.|Must|
|RBAC-007|Session revoke|Disabling a user shall revoke or invalidate active sessions promptly.|Must|
|RBAC-008|MFA|Support or plan MFA for privileged roles; strongly recommended before production<br>financial operations.|Should|



### **21. Audit Logs and Administrative Overrides** 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|AUD-001|Captured fields|Actor, role, tenant, action, entity type/id, timestamp, request/correlation ID,<br>IP/user-agent where appropriate, before/after summary for sensitive changes.|Must|
|AUD-002|Immutable|Audit events cannot be edited/deleted in ordinary product UI.|Must|
|AUD-003|Sensitive redaction|Secrets, full payment data and raw KYC document contents shall not be written<br>into audit payloads.|Must|
|AUD-004|Override reason|Super Admin override actions require reason/comment for financial, KYC,<br>suspension and permission-sensitive changes.|Must|
|AUD-005|High-risk events|Commission changes, wallet adjustments, payout state changes, KYC decisions,<br>suspension, customer reassignment and role changes shall be high-visibility audit<br>events.|Must|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 24 

VOKIT — Software Requirements Specification 

##### **21.1 Super Admin Override Rules** 

- Super Admin may override agency/customer status, feature gates, agent status, number assignment, plan assignment, KYC workflow, payout eligibility, payout state, wallet freezes and commission rate subject to role permission. 

- Overrides must not erase historical financial entries. Corrective financial action occurs through new ledger entries. 

- Where an override impacts customer production calls, UI shall display impact warning before confirmation. 

- Where feasible, dangerous actions require explicit confirmation and optional second approver for finance/compliancesensitive operations. 

### **22. Platform Settings** 

|**Setting Group**|**Examples**|
|---|---|
|Commercial|Currency, minimum withdrawal, maximum withdrawal, commissionable line-item policy, default plan|
|Payout|15-day hold duration default, 1–2 business-day SLA display, payout methods, business-day calendar|
|Telephony|Allowed countries, number capabilities, provider credentials, default call timeouts|
|AI|Approved LLM/STT/TTS providers/models, default voice/language, safety settings|
|Compliance|KYC gates, recording disclosure modes, retention periods, prohibited regions/use cases|
|Notifications|Email sender, templates, mandatory event categories|
|Security|Session duration, MFA enforcement, password policy, rate-limit thresholds|
|Feature flags|Integrations, outbound calling, recordings, customer edit permissions, templates|



### **23. Data Model and Entity Ownership** 

|**Entity**|**Owner**|**Key Data / Notes**|
|---|---|---|
|Agency|Platform|agency_id, owner_user_id, status, commission_rate, currency, kyc_status,<br>capabilities|
|AgencyKYC|Agency|kyc_id, status, submitted_at, reviewed_at, reviewer_id, reason_codes|
|KYCFile|AgencyKYC|file_id, type, storage_ref, hash, uploaded_at, visibility=internal|
|PayoutMethod|Agency|method_id, type, masked_details, verification_state|
|Customer|Agency|customer_id, agency_id, status, plan/subscription refs|
|User|Platform/Agency/Customer|user_id, identity, status|
|Role|Scope-specific|role_id, scope, permissions|
|Plan|Platform|plan_id/version, price, included_minutes, entitlements|
|Subscription|Customer|subscription_id, plan_version, cycle, status|
|Invoice|Customer|invoice_id, amount, currency, status, processor_ref|
|Payment|Customer|payment_id, invoice_id, amount, status, settled_at|
|CommissionEntry|Agency + Customer|entry_id, payment_id, eligible_base, rate_snapshot, amount, earned_at,<br>available_at, state|
|WalletLedgerEntry|Agency|ledger_id, type, amount, state, source_ref, actor|
|Payout|Agency|payout_id, amount, state, method, request/paid timestamps, receipt_ref|
|PayoutProof|Payout|proof_id, private file ref, admin metadata|
|Agent|Customer|agent_id, type, status, config/version refs|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 25 

VOKIT — Software Requirements Specification 

|AgentTemplate|Platform/Agency|template_id, version, visibility|
|---|---|---|
|KnowledgeSource|Global/Agency/Customer/Agent|source_id, owner_scope, processing_state|
|PhoneNumber|Platform/Agency/Customer|number_id, provider_ref, E164, state, cost, assignment|
|Call|Customer|call_id, provider_ref, agent_id, timestamps, status, usage/cost|
|CallArtifact|Call|recording/transcript/summary refs and retention metadata|
|IntegrationConnection|Agency/Customer|connection_id, provider, status, encrypted credential ref|
|AgentAction|Agent|action_id, type, schema, connection_ref|
|WebhookEndpoint|Agency/Customer|endpoint_id, URL, signing secret ref, status|
|WebhookDelivery|Endpoint|delivery_id, event_id, status, attempts|
|Notification|User/Tenant|notification_id, type, channel, delivery state|
|AuditEvent|Platform|event_id, actor, action, entity, tenant, timestamp, immutable payload|



### **24. State Machines and Workflow Rules** 

##### **24.1 Agency Status** 

|**State**|**Can Create**<br>**Customers**|**Can Create**<br>**Agents/Numbers**|**Can Request**<br>**Payout**|**Existing Customer Services**|
|---|---|---|---|---|
|Invited|No|No|No|N/A|
|Onboarding|No by default|No by default|No|N/A|
|Active|Yes if capability<br>enabled|Yes if entitled|Yes if KYC Verified|Active|
|Under Review|Configurable|Configurable|Usually No|Remain active unless separately disabled|
|Restricted|No by default|No/limited|No|Remain active unless separately disabled|
|Suspended|No|No new resources|No|Remain active or disabled per Super<br>Admin override|
|Closed|No|No|No|Terminated/migrated per closure process|



##### **24.2 Customer Status** 

|**State**|**Meaning**|
|---|---|
|Invited|Customer account exists; owner invitation pending|
|Active|Normal service|
|Payment Due|Payment issue; grace behavior configurable|
|Restricted|Some features disabled|
|Suspended|Production service restricted/disabled according to reason|
|Closed|No new service; retained records per policy|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 26 

VOKIT — Software Requirements Specification 

##### **24.3 Agent Status** 

|**State**|**Meaning**|
|---|---|
|Draft|Not production-ready|
|Testing|Available for test/simulator only|
|Active|Production routing enabled|
|Paused|Configuration retained, production handling disabled|
|Error|Operational/configuration problem|
|Archived|Removed from active use but retained for history|



##### **24.4 Commission State** 

|**State**|**Transition Rule**|
|---|---|
|Pending|Payment/eligibility not finalized|
|On Hold|Eligible earning, 15-day clock running|
|Available|Hold elapsed, not frozen/reversed|
|Frozen|Risk/admin hold|
|Reserved for Payout|Included in withdrawal|
|Paid|Settled through payout|
|Reversed|Commission negated by refund/dispute/correction|



##### **24.5 Payout State** 

|**State**|**Allowed Actions**|
|---|---|
|Requested|Review, freeze, reject, approve|
|Under Review|Approve, reject, freeze, request internal follow-up|
|Approved|Process, freeze/cancel if policy permits|
|Processing|Attach proof, mark paid, return for exception|
|Paid|Read-only financial terminal state; corrections use new records|
|Rejected|Terminal request state; eligible funds released|
|Frozen|Manual/compliance release or reject|



### **25. Security Requirements** 

|**ID**|**Area**|**Requirement**|**Priority**|
|---|---|---|---|
|SEC-001|Authentication|Use secure authentication for all portals; privileged operations require authenticated<br>server-side authorization.|Must|
|SEC-002|Authorization|Every protected request shall enforce RBAC and tenant ownership server-side.|Must|
|SEC-003|Secrets|API keys, OAuth refresh tokens, telephony/payment secrets and webhook signing keys shall<br>be stored encrypted/secret-managed and never exposed to client-side code.|Must|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 27 

VOKIT — Software Requirements Specification 

|SEC-004|Payments|Use payment processor tokenization/hosted fields where possible; Vokit shall not store raw<br>card security codes.|Must|
|---|---|---|---|
|SEC-005|Transport|All production traffic uses HTTPS/TLS.|Must|
|SEC-006|Sessions|Use secure, HttpOnly, SameSite-appropriate cookies or equivalent secure session<br>mechanism.|Must|
|SEC-007|CSRF|State-changing browser requests shall have CSRF protections appropriate to architecture.|Must|
|SEC-008|Rate limits|Rate-limit login, OTP, password reset, payout, webhook replay and resource-intensive<br>endpoints.|Must|
|SEC-009|Input validation|Validate/normalize all external input including URLs, phone numbers, webhook payloads<br>and integration responses.|Must|
|SEC-010|Webhook security|Validate inbound provider signatures and sign outbound tenant webhooks.|Must|
|SEC-011|File security|KYC/knowledge uploads shall enforce type/size policy and malware scanning where<br>infrastructure permits.|Should|
|SEC-012|Audit|Privileged and security-sensitive actions produce audit events.|Must|
|SEC-013|MFA|MFA should be required for Super Admin/Finance/KYC roles and available for agency<br>owners.|Should|
|SEC-014|Credential<br>rotation|Support rotating provider credentials and webhook signing secrets without data loss.|Should|
|SEC-015|No secret logging|Logs and error trackers shall redact credentials, payment secrets and sensitive document<br>content.|Must|



### **26. Privacy, Data Retention and Compliance Controls** 

Vokit shall provide technical controls needed to support applicable privacy, telephony, recording, KYC and payment obligations. Exact legal rules must be reviewed per operating jurisdiction before launch. 

|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|PRIV-001|Data minimization|Collect only data necessary for service, compliance and legitimate operations.|Must|
|PRIV-002|KYC segregation|KYC data receives restricted access and retention controls distinct from ordinary<br>customer data.|Must|
|PRIV-003|Call recording|Recording/transcription enablement shall be configurable by<br>region/customer/agent where required. Optional for user paid adon|Must|
|PRIV-004|Retention policy|Define configurable retention for recordings, transcripts, logs, KYC and financial<br>records, respecting legal minimum/maximum constraints.|Must|
|PRIV-005|Deletion requests|Support customer/agency data deletion workflow subject to financial/KYC/legal<br>retention exceptions.|Must|
|PRIV-006|Consent/disclosure|Support configurable call disclosure prompt/behavior where required.|Must|
|PRIV-007|Data export|Authorized tenant data export should be available for relevant operational data.|Should|
|PRIV-008|Subprocessors|Maintain provider/subprocessor inventory operationally outside or linked from<br>product settings.|Should|



### **27. Non-Functional Requirements** 

|**ID**|**Category**|**Requirement**|**Priority**|
|---|---|---|---|
|NFR-001|Availability|Target production availability should be defined (recommended ≥99.9% monthly|Should|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 28 

VOKIT — Software Requirements Specification 

|||excluding scheduled maintenance) for core portal/API; provider outages are tracked<br>separately.||
|---|---|---|---|
|||Typical authenticated portal API reads should target p95 < 800 ms excluding third-party||
|NFR-002|Performance|<br>provider latency.|Should|
|NFR-003|Call latency|Voice pipeline should minimize end-to-end conversational latency; platform shall<br>capture/provider latency diagnostics where feasible.|Should|
|NFR-004|Scalability|Architecture shall scale horizontally and avoid tenant-specific persistent process<br>assumptions.|Must|
|NFR-005|Idempotency|Financial, number-purchase, payment-webhook and payout-sensitive operations shall be<br>idempotent.|Must|
|NFR-006|Observability|Structured logs, metrics, traces/correlation IDs and alerting for critical workflows.|Must|
|NFR-007|Backups|Persistent databases/configuration shall have automated backup and tested recovery<br>strategy.|Must|
|NFR-008|Accessibility|Web portals should target WCAG 2.1 AA for core workflows.|Should|
|NFR-009|Browser|Support current major desktop browsers; customer/agency portals responsive for mobile<br>monitoring and basic actions.|Must|
|NFR-010|Timezones|Store timestamps in UTC and display in selected tenant/user timezone.|Must|
|NFR-011|Money|Store monetary values in integer minor units or safe decimal type with currency; never<br>binary floating-point for ledger math.|Must|
|NFR-012|Phone|Store normalized E.164 where applicable plus original/display formatting.|Must|
|NFR-013|Localization|Architecture should allow future localization; V1 language may be English.|Should|
|NFR-014|Maintainability|Business rules such as hold days, payout thresholds and commissionability must be<br>centralized/configurable rather than duplicated in UI code.|Must|



### **28. Error Handling and Edge Cases** 

|**Edge Case**|**Required Behavior**|
|---|---|
|Payment succeeds but webhook repeats|Idempotency key/provider event ID prevents duplicate invoice settlement or duplicate<br>commission.|
|Payment succeeds but internal commission<br>write fails|Retry/reconciliation job reconstructs missing commission from payment record; customer is<br>not double-charged.|
|Refund during 15-day hold|Reverse held commission before availability.|
|Refund after commission available|Debit available balance; if insufficient, create negative/receivable state according to policy.|
|Chargeback after payout paid|Create negative commission adjustment and freeze/review agency if required.|
|Agency changes commission rate|New eligible transactions use new effective rate; old commission entries retain snapshot.|
|Agency suspended while payout requested|Payout moves to Frozen/Under Review; no automatic payment.|
|KYC expires while wallet has available funds|Payout blocked until re-verification unless Super Admin overrides.|
|Payout marked paid accidentally|Do not delete/modify history; corrective workflow requires new reversal/adjustment with high-<br>level authorization.|
|Private payout proof missing|System should prevent Mark Paid if proof is mandatory by platform setting.|
|Number purchase provider succeeds but<br>local request times out|Reconciliation queries provider and imports/assigns or escalates orphaned number.|
|Customer out of minutes during call|Apply configured grace/overage behavior; do not abruptly terminate unless policy explicitly<br>requires.|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 29 

VOKIT — Software Requirements Specification 

|Integration timeout during call|Agent receives safe fallback, call continues where possible, error logged.|
|---|---|
|Knowledge ingestion fails|Existing published agent continues with last valid knowledge where safe; failed source clearly<br>flagged.|
|Agency attempts cross-tenant ID|Return authorization/not-found response without disclosing foreign tenant data.|
|Customer user edits restricted agent field|Server rejects even if client is manipulated.|
|Super Admin override affects active call|Warn and define whether change applies immediately or next call depending on setting type.|
|Payout request race condition|Atomic balance reservation ensures combined requests cannot exceed available balance.|



### **29. Reporting and Metrics** 

|**Audience**|**Metrics**|
|---|---|
|Super Admin|Total revenue, MRR, agencies, customers, agents, calls, minutes, AR/failed payments, commission liability,<br>held/available wallet, pending payouts, payout aging, KYC aging, provider costs, gross margin|
|Agency|Customer MRR, expected commission MRR, earned commission, held/available, lifetime paid, customers, agents,<br>calls, minutes, top customers, payout status|
|Customer|Plan, minutes used/remaining, call count/duration, agent activity, invoices/payment status, top-up history|
|Operations|Call failure rate, provider errors, integration failures, webhook delivery failure, number provisioning failures, agent<br>error rate|



|**ID**|**Requirement**|**Detailed Requirement**|**Priority**|
|---|---|---|---|
|RPT-001|Period filters|Reports support standard and custom periods.|Must|
|RPT-002|Tenant filters|Admin reports filter by agency/customer.|Must|
|RPT-003|Financial source|Financial reports derive from ledger/payment data, not UI-calculated estimates<br>alone.|Must|
|RPT-004|Export|CSV export should be available for financial/call operational lists with permission.|Should|
|RPT-005|Timezone|Report period calculations use explicitly selected reporting timezone.|Must|



### **30. API and Webhook Requirements** 

##### **30.1 API Principles** 

- REST or equivalent consistent API design with versioning strategy. 

- Server-side authorization on every endpoint. 

- Idempotency keys for payment-adjacent, number purchase, payout and other irreversible operations. 

- Pagination for list endpoints. 

- Stable machine-readable error codes plus human-readable messages. 

- Request/correlation IDs for support diagnostics. 

- Sensitive fields omitted or masked by role. 

##### **30.2 Outbound Event Catalog** 

|**Event**|**Trigger**|
|---|---|
|agency.created|Agency created|
|agency.status.changed|Agency activated/restricted/suspended/reactivated|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 30 

VOKIT — Software Requirements Specification 

|agency.kyc.submitted|KYC submitted|
|---|---|
|agency.kyc.status.changed|KYC decision/state changed|
|customer.created|Customer created|
|customer.status.changed|Customer state changed|
|invoice.created|Customer invoice created|
|invoice.paid|Invoice paid|
|payment.failed|Payment failed|
|commission.created|Commission created/held|
|commission.available|Hold elapsed and funds available|
|commission.reversed|Commission reversal|
|payout.requested|Agency requested payout|
|payout.status.changed|Payout status changed|
|payout.paid|Payout completed|
|agent.created|Agent created|
|agent.published|Agent activated|
|agent.status.changed|Agent status changed|
|call.started|Call started|
|call.answered|Call answered|
|call.completed|Call terminal state|
|call.transcript.ready|Transcript available|
|call.summary.ready|Summary available|
|agent.action.started|Agent tool/action started|
|agent.action.completed|Action completed|
|agent.action.failed|Action failed|
|knowledge.updated|Knowledge source ready/updated|
|phone_number.purchased|Number provisioned|
|phone_number.released|Number released|
|integration.failed|Integration error requiring attention|



##### **30.3 Webhook Payload Envelope** 

Recommended envelope fields: event_id, event_type, event_version, occurred_at, agency_id, customer_id (if applicable), object_id, data, delivery_id. Payloads shall exclude secrets and include only data appropriate to endpoint owner scope. 

### **31. Acceptance Criteria and Release Gates** 

##### **31.1 Functional Release Gates** 

- Agency can be created by Super Admin with commission rate and invitation. 

- Agency completes KYC; payout is blocked until Verified. 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 31 

VOKIT — Software Requirements Specification 

- Agency can create customer only when status/capability allows. 

- Customer can be assigned plan and pay Vokit directly. 

- Successful eligible payment creates exactly one commission entry with correct snapshot and 15-day availability date. 

- • Held funds are not withdrawable. 

- Available funds can be requested once and are atomically reserved. 

- Super Admin can review payout, upload private proof, mark Paid and trigger receipt generation. 

- Agency can view receipt but cannot access proof file. 

- Suspended agency cannot create customers and cannot bypass restriction by API manipulation. 

- Super Admin can override restrictions according to permission and every override is audited. 

- Agency can purchase/assign phone number and create/publish agent. 

- Incoming production calls reach correct tenant/customer agent and call record is written. 

- Customer portal shows only customer-owned agents/calls/invoices/usage. 

- Integrations/webhooks remain tenant-scoped and signed. 

- Refund/chargeback reverses/freezes commission correctly without rewriting historical ledger. 

- Roles prevent unauthorized KYC, payout, commission, cross-tenant and customer-agent actions. 

##### **31.2 Engineering / QA Release Gates** 

- Automated tests for commission and wallet state transitions. 

- Automated tenant isolation authorization tests. 

- Automated idempotency tests for payment webhooks and payout reservation. 

- Security review of authentication, RBAC, secrets, webhooks, uploads and payment integration. 

- Provider sandbox/end-to-end tests for number purchase and calls. 

- Backup/restore test for primary data store. 

- Observability dashboards/alerts configured for payment, payout, calling and integration failures. 

- Production runbook for payment reconciliation, payout exceptions, telephony incident, KYC issue and tenant suspension. 

### **32. Deferred / Post-V1 Scope** 

- Open agent marketplace with seller economics/revenue share 

- Advanced white-label custom domains and fully branded customer portals 

- Agency-defined retail pricing layers if Vokit later supports agency-controlled markup 

- Multi-level reseller/sub-agency hierarchy 

- Multi-currency settlement and automated FX 

- Automated KYC vendor decisioning beyond V1 workflow 

- Automated payout rails rather than Super Admin-assisted payout completion 

- Advanced outbound campaigns and dialer sequencing 

- Native mobile apps 

- Enterprise SSO/SAML 

- Advanced BI warehouse and cohort analytics 

- AI QA scoring/coaching and automated conversation grading 

- Complex CRM bidirectional sync framework 

- Public developer app marketplace 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 32 

VOKIT — Software Requirements Specification 

#### **Customer Risk, Payment Verification, Suspension and Chargeback Rules** 

- 

###### **1. Purpose** 

- This module defines the rules governing customer payment-risk detection, payment verification, customer suspension, chargebacks, permanent account restrictions, AI-agent shutdown, and agency commission reversals. 

- The objective is to protect Vokit, agencies, payment processors, and legitimate customers from fraudulent or unauthorized transactions. 

- Vokit retains final authority over all customer risk, suspension, verification, chargeback, and reactivation decisions. 

- 

- 

###### **2. Customer Risk Statuses** 

- Every customer shall have a payment-risk status. 

- Supported statuses: 

   - Normal 

   - Payment Review Required 

   - Verification Required 

   - Verification Submitted 

   - Under Review 

   - Verified 

   - Restricted 

   - Suspended 

   - Chargeback Frozen 

   - Permanently Banned 

• Risk status shall be independent from the customer's general account status but may automatically affect account functionality. 

- 

- **3. Risky Payment Detection** 

- When a customer invoice or payment is identified as potentially risky by Stripe or Vokit's internal risk controls, the customer shall automatically be placed into: 

- **Payment Review Required** 

- Risk triggers may include: 

   - Elevated or high payment-risk indication from Stripe 

   - Unusual payment behavior 

   - Billing information inconsistencies 

   - Cardholder information mismatch 

   - Multiple failed payment attempts 

   - Rapid changes in payment methods 

   - Abnormal purchase amounts 

   - Unusual geographic activity 

   - Fraud signals 

   - Previous payment disputes 

   - Previous verification failures 

   - Multiple customer accounts using related payment credentials 

   - Manual risk flag created by Super Admin 

- Vokit may introduce additional fraud-detection rules without requiring changes to the agency's configuration. 

- 

- 

###### **4. Agency Notification** 

- When customer verification is required, the responsible agency shall receive an immediate notification. 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 33 

VOKIT — Software Requirements Specification 

- The notification shall contain: 

   - Customer name 

   - Customer account ID 

   - Related invoice 

   - Payment amount 

   - Date of payment 

   - Payment verification status 

   - Required documents 

   - Submission deadline, where applicable 

- The agency shall be responsible for obtaining the required verification documents from its customer. 

- The agency shall not have authority to override or bypass the verification requirement. 

- 

- 

###### **5. Customer Payment Verification Requirements** 

- A customer flagged for payment verification must provide: 

- 

###### **5.1 Government-Issued Identification** 

- An acceptable government-issued identification document must be provided. 

- Examples may include: 

   - Passport 

   - National identity card 

   - Driving licence 

   - Other government-issued photo identification accepted by Vokit 

- The identification should contain sufficient information to verify the identity of the customer or authorized payer. 

- 

- 

###### **6. Payment Card Verification Image** 

- Where card ownership verification is required, the customer may be requested to provide an image of the physical payment card. 

- The system must enforce strict masking requirements. 

- 

- 

###### **Allowed card information** 

   - Only the following card-number information may remain visible: 

- **Last four digits** 

- Example: 

- •••• •••• •••• 4821 

- 

###### **Information that must be hidden** 

- The customer must conceal: 

   - All card-number digits except the final four digits 

   - CVV / CVC / security code 

   - Any other sensitive authentication data 

- The system must never request an image showing a complete payment card number. 

- 

- **7. Automated Card Image Validation** 

- The upload system shall validate the payment-card image before accepting it as a completed verification submission. 

- The system should attempt to determine whether more than the permitted last four card-number digits are visible. 

- If the system detects an exposed card number beyond the final four digits: 

- **The image must be rejected.** 

- 

   - The user shall receive a message similar to: 

- Your card image cannot be accepted because sensitive card-number information is visible. Please hide all card-number digits except the last four digits and upload the image again. 

- The verification submission shall remain incomplete until a compliant image has been provided. 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 34 

VOKIT — Software Requirements Specification 

- Where automated validation cannot confidently determine whether the card has been properly masked, the image may be placed into manual review rather than automatically approved. 

- 

- **8. Prohibited Card Data** 

- Vokit must not intentionally collect or retain: 

   - Full primary account numbers 

   - Full unmasked card numbers 

   - CVV/CVC values 

   - PIN numbers 

   - Magnetic-stripe data 

   - Chip authentication data 

   - Other prohibited sensitive card-authentication information 

- If an unmasked or improperly masked card image is inadvertently uploaded, it must not be treated as an acceptable verification document. 

- The platform should reject or securely remove such material according to Vokit's security and retention policies. 

- 

- 

###### **9. Verification Review** 

- Once required documents are submitted, the customer's status shall become: 

- **Verification Submitted** 

- and subsequently: 

- **Under Review** 

- Authorized Super Admin personnel shall be able to: 

   - Approve verification 

   - Reject verification 

   - Request new documents 

   - Request clearer documents 

   - Request additional information 

   - Suspend the customer 

   - Permanently ban the customer 

   - Override an automated risk decision where permitted 

- The agency may view the verification status but may not approve its own customer's payment verification unless explicitly permitted by Super Admin policy. 

- 

- **10. Verification Approval** 

- If payment verification is successfully completed, the customer status may return to: 

- **Verified / Active** 

- Any payment or service restrictions imposed solely because of the verification request may then be removed. 

- Approval shall not prevent Vokit from placing the customer into future reviews if new suspicious activity occurs. 

- 

- **11. Verification Failure** 

- Verification may be rejected where: 

   - Identity cannot be verified 

   - Documents appear altered 

   - Documents appear fraudulent 

   - Payment-card ownership cannot be reasonably established 

   - Customer refuses to provide requested verification 

   - Card image remains improperly masked 

   - Information does not match payment information 

   - Customer provides conflicting information 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 35 

VOKIT — Software Requirements Specification 

   - Vokit determines the transaction presents unacceptable risk 

- The customer may then be placed into: 

- **Restricted** or **Suspended** 

- depending on severity. 

- 

- **12. Restricted Customer Rules** 

- A restricted customer may be prevented from: 

   - Purchasing additional minutes 

   - Purchasing phone numbers 

   - Creating new AI agents 

   - Adding payment methods 

   - Upgrading plans 

   - Creating additional services 

- Existing agents may remain active during a normal risk review unless Super Admin determines that immediate service suspension is necessary. 

- Super Admin shall have authority to disable existing services at any time. 

- 

- 

###### **13. Customer Suspension** 

- An agency may request suspension of one of its customers where there is: 

   - Suspected fraud 

   - Payment failure 

   - Abuse 

   - Terms-of-service violation 

   - Identity concern 

   - Unauthorized usage 

   - Customer request 

   - Contract termination 

   - Other legitimate business reason 

- The agency's suspension authority must remain subordinate to Super Admin authority. 

- Super Admin may: 

   - Approve a suspension 

   - Directly suspend the customer 

   - Override agency actions 

   - Restore a customer 

   - Permanently ban the customer 

   - Suspend only billing functionality 

   - Suspend only new-resource creation 

   - Suspend all customer services 

• 

- 

###### **14. Chargeback Rule** 

- A confirmed payment chargeback shall trigger an immediate high-severity customer enforcement action. 

- 

   - The affected customer shall automatically enter: 

- **Chargeback Frozen** 

- unless Super Admin manually overrides the action in an exceptional case. 

- 

- 

###### **15. Immediate Chargeback Actions** 

- When a chargeback is received, the system shall automatically perform the following actions: 

   1. Freeze the customer account. 

   2. Disable customer portal access where appropriate. 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 36 

VOKIT — Software Requirements Specification 

   3. Stop all active AI agents belonging to that customer. 

   4. Prevent all customer AI agents from accepting new calls. 

   5. Prevent new outbound calls where supported. 

   6. Prevent the customer from purchasing additional minutes. 

   7. Prevent the customer from purchasing new phone numbers. 

   8. Prevent creation of new agents. 

   9. Prevent creation of new subscriptions. 

   10. Prevent new payment transactions except approved recovery payments. 

   11. Freeze any associated customer credits where applicable. 

   12. Notify the responsible agency. 

   13. Notify Super Admin. 

   14. Create an audit-log event. 

   15. Initiate commission reversal against the related agency. 

- 

   - No automatic restoration of the customer's AI agents shall occur after a chargeback. 

- 

- **16. AI Agent Shutdown** 

- When a customer enters Chargeback Frozen or Permanently Banned status, all agents belonging to the customer must immediately transition to a disabled state. 

- Example: 

- Active → Suspended 

- Suspended agents shall not: 

   - Accept inbound calls 

   - Initiate outbound calls 

   - Consume paid calling minutes 

   - Trigger chargeable AI activity 

   - Execute external automation actions unless specifically required for shutdown processing 

- The system shall retain configuration, call history, transcripts, audit information, and financial records for administrative and legal purposes. 

- 

- 

###### **17. Permanent Customer Ban After Chargeback** 

- A customer responsible for a confirmed chargeback may be designated: 

- 

###### **Permanently Banned** 

- Under the default Vokit policy, a customer that receives a confirmed chargeback shall no longer be eligible to onboard again to Vokit. 

- The restriction should apply across agencies. 

- An agency must not be permitted to recreate a permanently banned customer to bypass the restriction. 

- Where technically and legally appropriate, the system may maintain internal fraud-prevention identifiers associated with the banned customer. 

- Examples may include: 

   - Verified email address 

   - Phone number 

   - Customer identity 

   - Business information 

   - Payment processor customer identifiers 

   - Previous internal customer IDs 

   - Other fraud-prevention indicators permitted under Vokit policy 

- These indicators shall be used only for security, fraud prevention, compliance, and platform-protection purposes. 

- 

- **18. Re-Onboarding Prevention** 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 37 

VOKIT — Software Requirements Specification 

- During customer creation and onboarding, Vokit shall perform internal checks against permanently restricted customers. 

- If a matching permanently banned customer is identified: 

   - Customer onboarding must be blocked. 

   - The agency shall not be permitted to activate the customer. 

   - The system shall generate an internal risk event. 

   - Super Admin shall be notified. 

- The agency may be shown a generic message such as: 

- This customer is not eligible for onboarding on Vokit. 

- Internal fraud indicators or specific matching logic should not be disclosed to the agency. 

- • **19. Agency Commission Reversal on Chargeback** 

- Any agency commission generated from a customer payment that later results in a chargeback must be reversed. 

- The system must determine the original commission associated with the disputed transaction. 

- Example: 

- • Customer payment: **$100** • Agency commission: **30%** 

- Original agency commission: 

- • **+$30** • Chargeback: • Agency commission adjustment: • **-$30** • 

- **20. Commission Reversal During 15-Day Hold** 

- If the commission is still within its 15-day holding period: 

- On Hold → Reversed 

- The commission shall never become available for withdrawal. 

- Example: 

- Original Commission        +$30 

- Chargeback Reversal        -$30 

- Net Agency Earnings          $0 

- • **21. Commission Reversal From Available Balance** 

- If the commission has completed its 15-day hold and is already part of the agency's available wallet balance, the chargeback amount shall be deducted from the agency's available balance. 

- • Example: 

- Available Balance Before   $500 

- Commission Reversal         -$30 

- Available Balance After    $470 

- 

- **22. Commission Reversal From Pending Payout** 

- If the related commission is already included in a withdrawal request that has not yet been paid, Vokit may reduce, cancel, or recalculate the pending payout. 

- Example: 

- Requested Withdrawal       $500 

- Chargeback Adjustment       -$30 

- Adjusted Withdrawal        $470 

- The change must be recorded in the wallet ledger and payout audit history. 

- 

- **23. Commission Reversal After Agency Has Been Paid** 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 38 

VOKIT — Software Requirements Specification 

- If Vokit has already paid the related commission to the agency, the platform shall create a negative agency wallet balance or recover the amount from future commissions. 

- Example: 

- Commission Previously Paid   $30 

- Chargeback Adjustment        -$30 

- 

- Agency Wallet                -$30 

- Future commissions shall first satisfy the negative balance. 

- Example: 

- Existing Balance             -$30 

- New Commission               +$50 

- Available After Recovery     $20 

- Super Admin may also recover the amount through another approved settlement mechanism where necessary. 

- 

- **24. Agency Responsibility for Customer Chargebacks** 

- Agencies are responsible for commissions they receive from transactions subsequently reversed through valid refunds, disputes, fraud reversals, or chargebacks. 

- An agency may not retain commission generated from revenue that Vokit ultimately does not retain. 

- The agency agreement should explicitly disclose this rule. 

- 

- **25. Agency Risk Monitoring** 

- Agencies with excessive customer fraud, payment disputes, chargebacks, or suspicious activity may themselves be placed under review. 

- The system should allow Super Admin to monitor: 

   - Total customer payments 

   - Number of disputes 

   - Chargeback count 

   - Chargeback value 

   - Chargeback ratio 

   - Verification-request count 

   - Verification failure count 

   - Permanently banned customers 

   - Commission reversals 

   - Negative agency balance 

- Repeated or abnormal patterns may result in agency restrictions or suspension. 

- 

- **26. Agency Suspension Related to Customer Fraud** 

- Where Super Admin determines that an agency is associated with suspicious customer activity, Super Admin may: 

   - Freeze agency payouts 

   - Freeze available wallet balance 

   - Prevent customer creation 

   - Prevent new agent creation 

   - Prevent phone-number purchases 

   - Require additional KYC 

   - Require business re-verification 

   - Place the agency under investigation 

   - Suspend the agency 

   - Permanently terminate the agency 

- Existing customer services may be handled separately according to Super Admin's determination. 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 39 

VOKIT — Software Requirements Specification 

- 

- **27. Super Admin Override Authority** 

- Super Admin shall retain complete overriding authority over: 

   - Customer risk status 

   - Customer verification 

   - Customer suspension 

   - Customer reactivation 

   - Permanent customer bans 

   - Agency restrictions 

   - Agency suspension 

   - Agent suspension 

   - Payment verification requirements 

   - Commission reversals 

   - Wallet adjustments 

   - Payout freezes 

   - Chargeback actions 

   - Exceptional customer recovery 

###### • 

   - All manual overrides must generate an immutable audit-log entry containing: 

   - Admin user 

   - Action performed 

   - Previous status/value 

   - New status/value 

   - Reason 

   - Date and time 

   - Related customer 

   - Related agency 

   - Related payment/invoice where applicable 

- 

- 

###### **28. Customer and Agency Notifications** 

- The agency shall receive notifications for major risk events, including: 

   - Customer verification required 

   - Verification submitted 

   - Verification approved 

   - Verification rejected 

   - Customer restricted 

   - Customer suspended 

   - Chargeback received 

   - Customer permanently banned 

   - Commission reversed 

   - Payout adjusted due to chargeback 

- Customers may receive suitable notifications depending on the event and Super Admin policy. 

- Vokit may withhold sensitive fraud-detection information from both customers and agencies. 

- 

###### • 

###### **29. Audit Requirements** 

- The following events must be permanently auditable: 

   - Stripe risk flag received 

   - Verification requested 

   - ID uploaded 

   - Masked card image uploaded 

Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 40 

VOKIT — Software Requirements Specification 

   - Card image rejected 

   - Verification approved 

   - Verification rejected 

   - Customer restricted 

   - Customer suspended 

   - Chargeback received 

   - Agent shutdown initiated 

   - Customer permanently banned 

   - Re-onboarding attempt blocked 

   - Commission reversal 

   - Payout adjustment 

   - Agency risk action 

   - Super Admin override 

- Financial and risk audit records must not be removable through standard user interfaces. 

- 

- **30. Core Business Rules Summary** 

   1. Risky Stripe payments may trigger mandatory customer payment verification. 

   2. Required verification may include government-issued identification and a masked payment-card image. 

   3. Payment-card images must reveal no more than the final four card-number digits. 

   4. CVV/CVC and other sensitive authentication data must never be accepted as verification information. 

   5. Non-compliant card images must be rejected. 

   6. Agencies cannot bypass mandatory Vokit verification. 

   7. Super Admin has final authority over every risk and suspension decision. 

   8. A confirmed chargeback freezes the affected customer. 

   9. All agents belonging to a chargeback-frozen customer are immediately disabled. 

   10. Permanently banned customers cannot onboard again through another Vokit agency. 

   11. Commission earned from a charged-back payment must be reversed. 

   12. Reversal first applies to held commission, then available wallet balance, then pending payout, and finally creates a negative agency balance where the commission has already been paid. 

   13. Future agency commissions must offset any negative wallet balance before new withdrawals become available. 

   14. Excessive fraudulent customers or chargebacks may trigger investigation or suspension of the agency itself. 

   15. Every financial, verification, suspension, and override action must be auditable. 

### **Appendix A — Permission Matrix** 

|**Capability**|**Super Admin**|**Agency**|**Customer**|
|---|---|---|---|
|View all agencies|Yes|Scoped|No|
|Create agency|Yes|No|No|
|Set agency commission|Authorized Admin|No|No|
|Review KYC|Authorized Admin|Own submission only|No|
|View KYC documents|KYC-authorized only|Own submission only|No|
|Create customer|Yes|If Active/capability enabled|No|
|View other agency customer|Yes|No|No|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 41 

VOKIT — Software Requirements Specification 

|Create agent|Yes|Agency scope|Only if explicitly permitted|
|---|---|---|---|
|Purchase number|Yes|Agency scope if enabled|No by default|
|View calls|All subject to role|Agency scope|Customer scope|
|View platform cost|Authorized Admin|No|No|
|View customer invoices|Yes|Agency customers|Own customer|
|Pay invoice|Support/admin if enabled|No|Yes|
|View agency wallet|Finance/admin|Own agency|No|
|Request payout|No (admin processes)|Agency finance/owner|No|
|Approve payout|Authorized Finance Admin|No|No|
|Upload payout proof|Authorized Finance Admin|No|No|
|View payout proof|Authorized Finance Admin|No|No|
|View payout receipt|Yes|Own agency|No|
|Suspend agency|Authorized Admin|No|No|
|Override restrictions|Authorized Admin|No|No|
|Manage platform roles|Authorized Admin|No|No|
|Manage agency team|Support/admin|Agency owner/admin|No|
|Manage customer team|Support/admin|Agency if allowed|Customer owner/admin|



### **Appendix B — Event Catalog** 

See Section 30.2 for V1 outbound webhook events. Internal domain events should mirror the same lifecycle semantics and drive notifications, audit, reporting and integration delivery using idempotent consumers. 

### **Appendix C — Financial Examples** 

**Example 1: Normal Subscription Commission** 

|**Step**|**Amount / State**|
|---|---|
|Customer pays Vokit|$100.00 invoice paid|
|Commission rule|30% on eligible $100|
|Agency commission|$30.00 — On Hold|
|Platform gross share before costs|$70.00|
|Availability|Commission becomes Available after 15 days if no freeze/reversal|
|Payout|Agency later requests any amount up to Available balance|



**Example 2: Multiple Independent Holds** 

|**Payment**|**Commission**|**Earned**|**Available**|
|---|---|---|---|
|$100|$30|Sep 1|Sep 16|
|$150|$45|Sep 5|Sep 20|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 42 

VOKIT — Software Requirements Specification $66.67 $20 Sep 10 Sep 25 

##### **Example 3: Refund During Hold** 

A $100 payment created $30 commission On Hold. Customer is fully refunded before day 15. The $30 commission is reversed and never reaches Available balance. 

##### **Example 4: Chargeback After Payout** 

A $30 commission was already included in a completed payout. A later chargeback reverses the underlying payment. Vokit creates a -$30 commission/ledger adjustment. The agency may show a negative available balance or future earnings may offset the amount according to platform policy. Historical payout remains Paid and is not rewritten. 

##### **Example 5: Commission Rate Change** 

Agency rate changes from 20% to 30% effective September 10. A payment settled September 9 uses 20%; a qualifying payment settled September 10 or later uses 30%. Each commission record stores its rate snapshot. 

### **Appendix D — Glossary** 

|**Term**|**Definition**|
|---|---|
|Agency|A Vokit reseller/service agency that creates and manages AI voice services for its customers.|
|Customer|An end business serviced by an agency through Vokit.|
|Customer MRR|Qualifying recurring subscription revenue billed to agency customers by Vokit.|
|Expected Commission MRR|Expected recurring agency commission derived from commissionable recurring customer revenue.|
|Commission|Agency earning calculated from eligible customer revenue using configured rate/rules.|
|On Hold|Commission not withdrawable until its individual 15-day hold and other eligibility rules are satisfied.|
|Available Balance|Agency wallet amount currently eligible for withdrawal.|
|Payout|Transfer of eligible agency wallet funds from Vokit to agency payout method.|
|Payout Proof|Private internal evidence uploaded by Super Admin confirming external payout action.|
|Payout Receipt|Agency-visible Vokit-generated confirmation of a completed payout.|
|KYC|Know Your Customer/Business identity and verification workflow applied to agencies.|
|Agent|Configured AI voice application that handles phone conversations and permitted actions.|
|Knowledge Source|Content available to an agent through controlled retrieval.|
|Tool / Action|Explicit operation an agent may invoke, often backed by integration or webhook.|
|Super Admin Override|Authorized platform action that supersedes tenant controls without erasing audit/history.|
|Ledger|Immutable sequence of financial entries used to derive balances and reconcile funds.|



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 43 

VOKIT — Software Requirements Specification 

### **SRS Baseline Sign-off** 

This SRS defines the V1 product baseline. Implementation stories, database schema, API contracts, UI wireframes, test cases and operational runbooks should trace back to the requirement IDs and business rules in this document. 

|**Role**|**Name**|**Approval**|**Date**|
|---|---|---|---|
|Product Owner||||
|Engineering Lead||||
|QA Lead||||
|Finance / Operations||||
|Compliance / Legal Review||||



Vokit V1 Agency Platform  |  SRS v1.0  |  Confidential  |  Page 44 

