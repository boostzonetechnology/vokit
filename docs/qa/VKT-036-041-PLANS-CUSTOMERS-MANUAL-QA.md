# VKT-036 → VKT-041 — Manual QA (Plans + Customers)

**Language:** Roman Urdu (tester-friendly)  
**Scope:** Plan catalog, entitlements, customer directory/create, plan assign/change, minutes, status, agency list/create/detail  
**SoT:** SRS PLAN-001..007, SA3-001..005; ADR-011; `docs/flows/plans/PLAN-CREATE-ASSIGN-CAPS.md`  
**Jira:** VKT-036, VKT-037, VKT-038, VKT-039, VKT-040, VKT-041  

Yeh doc **code folder names** nahi — **sidebar / page / button** names se chalati hai taake UI mein module dhoondna asaan ho.

---

## 0) Pehle yeh samajh lo (map)

| Task | Kya prove karna hai | Portal | Sidebar / URL | Screen pe kya dikhega |
|---|---|---|---|---|
| **VKT-036** | Plan create, version, entitlements, archive | **Platform (Super Admin)** | Left nav → **Plans** → `/plans` | Title **Plans**, button **Create plan**, tabs **Entitlements / Versions / Assignment / Grandfathering** |
| **VKT-037** | Global customer directory (filter + plan/minutes columns) | Platform | Left nav → **Customers** → `/customers` | Title **Customers**, table **Directory** columns: Customer, Agency, Status, Plan, Minutes, Updated |
| **VKT-038** | Super Admin customer create | Platform | **Customers** → button **Create customer** → `/customers/new` | Steps **Account** → **Profile** |
| **VKT-039** | Assign/change plan, minutes adjust, suspend | Platform | **Customers** → row click → `/customers/{id}` | Tabs **Overview / Minutes / Plan / Status** |
| **VKT-040** | Agency customer list + create | **Agency** | Left nav → **Customers** → `/customers` | Title **Customers**, create flow agency ke under |
| **VKT-041** | Agency customer detail (plan + status + invite) | Agency | Customer row → `/customers/{id}` | Tabs **Overview / Invite / Plan / Status / Resources** |

### Portals (local)

| Portal | App | Typical URL | Login role |
|---|---|---|---|
| Platform / Super Admin | `apps/web-platform` | `http://localhost:5173` | Platform staff (plans + customers perms) |
| Agency | `apps/web-agency` | `http://localhost:5174` | Agency user (`customer.*`, plans catalog read) |
| Customer (invoice pay) | `apps/web-customer` | customer portal | Customer owner — **Pay invoice** ke liye |

### Price note (important)

UI pe **Price (minor)** = cents.  
`10000` = **$100.00** · `5000` = **$50.00** · `25000` = **$250.00**

### Caps note (important)

`Max agents / phone numbers / concurrency` mein **`0` = unlimited**.  
Empty **Allowed integrations** = saari providers allowed.

### Change plan rule (VKT-039 / ADR-011)

| Situation | System kya karega |
|---|---|
| Nayi price **zyada** | **Upgrade** → open invoice + unused-time credit; pay ke baad plan switch |
| Nayi price **kam** | **Downgrade** → period end pe schedule (agar extras fit hon) |
| Same price lekin caps/integrations **tight** | Bhi **downgrade** treat (period end) |
| Same price + entitlements tight nahi | Turant **applied** |
| Already same version | Reject (`same_plan_version`) |
| Upgrade invoice open / due | Naya change block (`subscription_change_pending`) |

---

## 1) Test shuru karne se pehle (setup checklist)

Pass karo warna false bugs aayenge:

- [ ] API chal rahi ho (`manage.py runserver`)
- [ ] Control-plane migrate: `python manage.py migrate`
- [ ] Tenant migrate: `python manage.py migrate_tenants` (warna subscription/change pe 500 / missing column)
- [ ] Dummy payment processor chal raha ho (invoice pay ke liye) — `packages/dummy-payment-processor` on **8081**: `php -S 127.0.0.1:8081 -t public`
- [ ] `apps/api/.env` mein `SANDBOX_WEBHOOK_SECRET` set ho aur **dummy** `.env` ke sath **exact match** (example: `local-dev-sandbox-webhook`). Warna Pay pe message aayega lekin invoice **open** hi rahegi (API log: `POST /webhooks/sandbox/v1/` → **503**)
- [ ] Secret change ke baad API server **restart**
- [ ] Kam az kam **1 Active agency** maujood ho (Platform → **Agencies**)
- [ ] Platform user ke paas plans + customers permissions hon
- [ ] Agency user usi agency ka ho jahan customers test karoge
- [ ] Browser fresh login; Network tab open rakhna optional (500 vs 409 alag dikhte hain)

**Bug report format (har fail pe):**

```text
Task: VKT-0xx
Step: …
Expected: …
Actual: …
Portal/URL: …
Screenshot / Network status + error code: …
```

---

## 2) Master end-to-end flow (ek hi kahani — 036→041)

Yeh **poora happy path** hai. Is ko pehle ek dafa full chalao. Phir neeche negative cases.

### Step A — Do plans banao (VKT-036)

1. Platform login → left nav **Plans**.
2. **Create plan** click.
3. Plan A banao — name: `QA Basic`, price minor `10000`, included minutes `100`, max agents `0`, max numbers `0`, recording checked, integrations empty.
4. Save / **Create plan**.
5. Left list mein plan select karo → tab **Entitlements** pe price/minutes/caps sahi dikhne chahiye.
6. Tab **Versions** → **Add version** se Plan A ka v2: price `15000` (upgrade target).
7. Dubara **Create plan** → Plan B: name `QA Pro`, price `25000`, included `200`, max agents `5`, max numbers `3`, max concurrency `2`, integrations mein ek slug (jaise `n8n` agar list mein ho).

**Pass:** dono plans **active**; versions list mein v1/v2; Entitlements tiles sahi.

### Step B — Global directory empty/list (VKT-037)

1. Left nav **Customers**.
2. Page title **Customers** + **Create customer** button dikhe.
3. Filters try: **Search**, **Agency**, **Status**.
4. Table columns: Customer | Agency | Status | Plan | Minutes | Updated.

**Pass:** page 500 nahi; filters crash nahi; empty state message OK.

### Step C — Super Admin customer create (VKT-038)

1. **Create customer**.
2. Step **Account**: Agency select (jo Active ho), Display name `QA Cust 1`, Owner email unique.
3. **Next** → Step **Profile**: legal/phone/country/timezone optional fill.
4. Submit.

**Pass:** customer detail pe land / list mein naya row; status invited/active policy ke mutabiq; agency usi selected agency ki.

### Step D — First plan assign + pay (VKT-039 + billing)

1. Customer detail → tab **Plan**.
2. Agar subscription nahi: dropdown **Plan version** → `QA Basic v1` → **Assign plan**.
3. Message: invoice generate / assigned.
4. Customer portal se us invoice ko **Pay** karo (dummy processor), YA lab flow se settle karo.
5. Wapas Platform customer → **Plan** tab: Plan name, Version, Status **active**, Included minutes, **Period end** date (dash `—` nahi hona chahiye after fix), Pending **None**.
6. Tab **Minutes**: remaining minutes / lots dikhne chahiye (assign+pay ke baad included minutes).

**Pass:** second time **Assign plan** fail with clear error (subscription already exists) — change use karo.

### Step E — Directory enrichment (VKT-037 verify)

1. Wapas **Customers** list.
2. `QA Cust 1` row: **Plan** column mein plan name, **Minutes** number (0+).

**Pass:** Plan/Minutes `—` nahi agar subscription+usage maujood.

### Step F — Upgrade (higher price) (VKT-039)

1. Detail → **Plan** → **Change to plan version** → `QA Basic v2` ($150) YA `QA Pro v1` ($250).
2. **Change plan**.
3. Expect: upgrade message + **upgrade invoice** total (proration credit ke baad).
4. Plan tab pe pending upgrade / invoice hint.
5. Invoice **pay** karo.
6. Refresh: naya plan version active; period restart feel (period end update); pending clear.

**Pass:** pay se pehle old version pe rehna; pay ke baad new version.

### Step G — Downgrade / tighter (VKT-039)

1. Ab higher plan se wapas cheaper / tighter pe change try:
   - Example: Pro ($250, caps 5/3/2) → Basic ($100, unlimited 0) — yeh **price kam** = downgrade schedule.
   - YA same price lekin integrations/caps tight.
2. **Change plan**.

**Pass:**

- Kind **downgrade** / message period end schedule.
- **Pending change** tile pe `downgrade` + date.
- Turant plan name purana reh sakta hai (apply period end pe).
- Agar customer pe **zyada active agents / assigned numbers** hain target se → error extras exceed (clear message), 500 nahi.

### Step H — Minutes adjust (VKT-039)

1. Tab **Minutes**.
2. Credit: minutes `+25`, reason `QA credit` → submit.
3. Remaining badhna chahiye.
4. Debit: `-10`, reason `QA debit`.
5. Reason empty → validation fail (no silent 500).

### Step I — Status / suspend (VKT-039)

1. Tab **Status**.
2. Allowed action (suspend / etc.) + reason jahan required.
3. Confirm.
4. Header badge status update; list filter **Status** se bhi dikhe.

### Step J — Agency list/create (VKT-040)

1. **Agency portal** login (usi agency ka).
2. Left nav **Customers**.
3. Sirf **apni agency** ke customers dikhne chahiye (Platform wale dusri agency ke nahi).
4. Create customer (agency form) → apni agency ke under.

**Pass:** cross-agency customer list mein nahi.

### Step K — Agency detail plan/status (VKT-041)

1. Agency → customer open.
2. Tabs: **Overview**, **Invite**, **Plan**, **Status**, **Resources**.
3. **Plan** tab: assign (agar nahi) / **Change plan** (agar hai) — Platform jaisa rule.
4. **Invite**: email + role → invite success/error clear.
5. **Status**: agency-allowed transitions.
6. Optional: Agency left nav **Plans** → Billing screen tab **Plan catalog** — sirf **active** plans read-only (create nahi).

**Pass:** agency dusri agency ke customer id URL se open kare → not found / hidden (500 leak nahi).

---

## 3) Task-wise checklist (SRS / DoD)

### VKT-036 — Plans (PLAN-001..007, PLAN-005 entitlements)

| # | Case | Steps | Expected | P/F |
|---|---|---|---|---|
| 36.1 | Create plan | Plans → Create plan → fill terms → save | Plan active + v1 | |
| 36.2 | Entitlements show | Select plan → Entitlements | Price, minutes, topups, overage, grace, max agents/numbers/concurrency, recording, integrations | |
| 36.3 | Add version | Versions → Add version (new price) | New version number; old subscriptions purani version pe rehti hain (message) | |
| 36.4 | Immutable after use | Assign plan kisi customer ko → us version pe edit/PATCH try (agar UI edit hai) | Used version change block / immutable | |
| 36.5 | Archive | Archive button | Status archived; assignable nahi | |
| 36.6 | 0 = unlimited | Caps 0 set | Entitlements tile pe Unlimited-style | |
| 36.7 | Assignment tab | Assignment se customer + version assign | Invoice / success (ya detail se assign — dono allowed paths) | |

### VKT-037 — Global directory (SA3-001)

| # | Case | Steps | Expected | P/F |
|---|---|---|---|---|
| 37.1 | Open directory | Customers | 200, no unexpected error | |
| 37.2 | Search | Name type | Debounce ke baad filter | |
| 37.3 | Agency filter | Ek agency select | Sirf us agency ke rows | |
| 37.4 | Status filter | active / suspended… | Match | |
| 37.5 | Plan column | Subscribed customer | Plan name (+ version) | |
| 37.6 | Minutes column | After usage | Number, not always — | |
| 37.7 | Open detail | Row click / Open → | `/customers/{id}` | |

### VKT-038 — Platform create (SA3-002)

| # | Case | Steps | Expected | P/F |
|---|---|---|---|---|
| 38.1 | Required Account | Agency/name/email khali | Step error, no create | |
| 38.2 | Happy create | Valid Account + Profile | Customer created under selected agency | |
| 38.3 | Duplicate / ban | Banned email/policy agar lab data ho | Clear reject, no stacktrace | |
| 38.4 | Wrong agency | Inactive/suspended agency (agar UI allow) | Policy reject | |

### VKT-039 — Assign / change / minutes / status (SA3-003..005, PLAN-007)

| # | Case | Steps | Expected | P/F |
|---|---|---|---|---|
| 39.1 | First assign | Plan → Assign plan | Open invoice; subscription active after pay path | |
| 39.2 | Double assign | Assign dubara | Clear conflict, not 500 | |
| 39.3 | Upgrade | Higher price Change plan | Invoice + pending upgrade | |
| 39.4 | Pay upgrade | Customer pay | Switch version; pending clear | |
| 39.5 | Unpaid upgrade block | Open upgrade pe naya change | Blocked pending | |
| 39.6 | Downgrade schedule | Lower price Change plan | pending downgrade @ period end | |
| 39.7 | Same version | Current version select | Reject same plan version | |
| 39.8 | Same $ applied | Same price, not tighter | Applied immediately | |
| 39.9 | Minutes +/- | Minutes tab | Ledger-backed remaining change; reason required | |
| 39.10 | Suspend | Status tab | Status change + list reflect | |
| 39.11 | Period end shown | Plan tab | Period end date visible | |
| 39.12 | No 500 on change | Naive datetime / schema | Change plan never “unexpected error” for valid case | |

### VKT-040 — Agency list/create

| # | Case | Steps | Expected | P/F |
|---|---|---|---|---|
| 40.1 | Agency list | Agency → Customers | Only own customers | |
| 40.2 | Create | Create under agency | Appears in agency list + platform directory under that agency | |
| 40.3 | Isolation | Forge other agency customer URL | Hidden / not found | |

### VKT-041 — Agency detail

| # | Case | Steps | Expected | P/F |
|---|---|---|---|---|
| 41.1 | Tabs load | Open detail | Overview/Invite/Plan/Status/Resources no crash | |
| 41.2 | Assign/change | Plan tab | Same billing rules as platform (perms allow) | |
| 41.3 | Invite | Invite tab | Invite accepted/error mapped | |
| 41.4 | Status | Status tab | Allowed transitions only | |
| 41.5 | Resources | Resources tab | Counts/links sensible (agents/numbers) | |

---

## 4) Negative / adversarial (must run)

| # | Attack / mistake | Kaise | Expected |
|---|---|---|---|
| N1 | Agency A user → Agency B customer detail URL | Browser URL mein dusra id | No data leak |
| N2 | Customer user plan create try | Customer portal / API | Forbidden |
| N3 | Agency plan create try | Agency Plans catalog | Create nahi; read-only active |
| N4 | Change without subscription | Plan change pehle assign ke | subscription_required style error |
| N5 | Downgrade jab 6 agents active, target max 5 | Change plan | extras_exceed_plan, agents pehle pause/archive |
| N6 | Cap enforcement | Plan max_agents=1 → 2nd active agent | plan_limit_agents |
| N7 | Integration allowlist | Plan only `n8n` → connect dusra | plan_integration_not_allowed |
| N8 | Recording blocked | recording_allowed off → enable disclosure | plan_recording_disabled |
| N9 | Tenant migration skip | Purani tenant DB | Fail closed / migrate_tenants; not silent wrong data |
| N10 | CSRF / unauth POST | Logged out change plan | 401/403, not 500 |

---

## 5) Suggested lab data (copy-paste)

| Entity | Suggested values |
|---|---|
| Plan A | `QA Basic` · price `10000` · minutes `100` · agents `0` · numbers `0` |
| Plan A v2 | price `15000` · minutes `150` |
| Plan B | `QA Pro` · price `25000` · minutes `200` · agents `5` · numbers `3` · concurrency `2` · integrations `n8n` |
| Customer | `QA Cust 1` · unique owner email |
| Minutes credit | `+25` reason `QA credit` |
| Minutes debit | `-10` reason `QA debit` |

---

## 6) UI cheezein — naam se dhoondo (confusion avoid)

| Tum soch rahe ho | Asal UI |
|---|---|
| “Plan module” | Platform sidebar **Plans** (page title **Plans**) |
| “Customer module” | Sidebar **Customers** (directory / create / detail) |
| “Plan change screen” | Customer **detail** → tab **Plan** → **Change to plan version** + **Change plan** |
| “Balance / minutes” | Customer detail → tab **Minutes** (Platform). Agency detail pe resources alag tab |
| “Agency plans” | Agency sidebar **Plans** → Billing screen, tab **Plan catalog** (read catalog) |
| “Pay invoice” | **Customer** portal billing → **Pay / receipts** (Super Admin assign ke baad invoice pay yahan) |
| “Suspend” | Customer detail → tab **Status** (Platform + Agency) |

Code folders (`features/plans`, `features/customers`) tester ko dhoondne ki zaroorat nahi — sidebar se kaafi hai.

---

## 7) Sign-off sheet

| Area | Tester | Date | Result (Pass/Fail) | Notes |
|---|---|---|---|---|
| Master E2E §2 | | | | |
| VKT-036 | | | | |
| VKT-037 | | | | |
| VKT-038 | | | | |
| VKT-039 | | | | |
| VKT-040 | | | | |
| VKT-041 | | | | |
| Negatives §4 | | | | |

**Exit:** Critical/High open nahi (500 on happy path, tenant leak, wrong plan switch without pay, minutes without reason/ledger). Medium UX gaps note karke sign-off with risk accept.

---

## 8) Related docs

- Flow (technical): `docs/flows/plans/PLAN-CREATE-ASSIGN-CAPS.md`
- ADR: `docs/adr/ADR-011-plan-entitlements-and-proration.md`
- Global QA strategy: `docs/execution/17-QA-TESTING-PLAN.md`
