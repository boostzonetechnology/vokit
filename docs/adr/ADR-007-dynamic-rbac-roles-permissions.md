# ADR-007 — Dynamic DB-Backed RBAC: Roles & Permissions

**Status:** Accepted  
**Date:** 2026-09-12  
**SRS refs:** SA12 (RBAC), SA18 (Sensitive permissions), SA-TEAM (Invitation)

---

## Context

Phase 2 shipped a static `ROLE_PERMISSIONS` dict in `domain/roles.py`. All permission checks read from that in-process dict. This prevents:

- Adding / removing permissions per role without a code deploy.
- Auditing which roles have which permissions.
- Building a self-service RBAC admin UI (Phase 5+).
- Using stable FK references from `Membership` and `Invitation` rows to a `Role` record.

Existing permission codes used dot notation with plural nouns (`agencies.view`, `recordings.hold`) and mixed verbs (`manage`, `review`, `configure`). These are inconsistent and make programmatic CRUD mapping ambiguous.

---

## Decision

### 1. Permission model (new codes)

Permissions are stored in `identity_permissions` with a `(namespace, code)` unique constraint.

Code format: `{module}.{action}` where module is **singular** and action is one of:

| Action | Meaning |
|--------|---------|
| `view` | Read/list |
| `create` | Create new record |
| `update` | Modify existing |
| `delete` | Remove / disable |
| `hold` | Specific sensitive retain action |
| `request` | Initiate a workflow (payout.request) |
| `approve` | Approve a sensitive workflow |
| `adjust` | Financial adjustment |
| `pay` | Customer billing pay |
| `verify` | KYC / risk verify |
| `review` | Platform-level sensitive review |
| `connect` | Third-party integration connect |
| `provision` | Provision a new resource |
| `migrate` | Run schema/tenant migration |
| `route` | Tenant DB routing admin |
| `sync` | Sync permission catalog |
| `use` | Use an action (impersonation) |

Permissions are namespaced to `platform`, `agency`, or `customer` — no permission code is valid across namespaces.

### 2. Old → New code mapping

| Old code | New code(s) | Namespace |
|----------|-------------|-----------|
| `agencies.view` | `agency.view` | platform |
| `agencies.create` | `agency.create` | platform |
| `agencies.manage` | `agency.update` + `agency.delete` | platform |
| `customers.view` | `customer.view` | platform |
| `customers.create` | `customer.create` | platform |
| `customers.manage` (agency) | `customer.view`, `customer.create`, `customer.update`, `customer.delete` | agency |
| `plans.manage` | `plan.view`, `plan.create`, `plan.update`, `plan.delete` | platform |
| `settings.manage` | `setting.view`, `setting.update` | platform |
| `notifications.manage` | `notification.view`, `notification.create`, `notification.update`, `notification.delete` | platform |
| `agents.review` | `agent.view` | platform |
| `agents.manage` | `agent.view`, `agent.create`, `agent.update`, `agent.delete` | agency |
| `agents.view` | `agent.view` | customer |
| `numbers.review` | `number.view` | platform |
| `numbers.manage` | `number.view`, `number.create`, `number.update`, `number.delete` | agency |
| `transfers.review` | `transfer.view` | platform |
| `transfers.manage` | `transfer.view`, `transfer.create`, `transfer.update`, `transfer.delete` | agency |
| `calls.review` / `calls.view` | `call.view` | platform / agency / customer |
| `recordings.review` / `recordings.view` | `recording.view` | platform / agency / customer |
| `recordings.hold` | `recording.hold` | agency (sensitive) |
| `integrations.review` / `integrations.view` | `integration.view` | platform / agency / customer |
| `integrations.manage` | `integration.view`, `integration.create`, `integration.update`, `integration.delete` | agency |
| `integrations.connect` | `integration.connect` | customer |
| `webhooks.manage` | `webhook.view`, `webhook.create`, `webhook.update`, `webhook.delete` | agency |
| `notices.configure` | `notice.view`, `notice.update` | agency / customer |
| `users.invite` | `user.create` | platform |
| `users.disable` | `user.delete` | platform |
| `team.invite` | `team.create` | agency / customer |
| `team.disable` | `team.delete` | agency / customer |
| `tenants.view` | `tenant.view` | platform |
| `tenants.provision` | `tenant.provision` | platform |
| `tenants.migrate` | `tenant.migrate` | platform |
| `tenants.route` | `tenant.route` | platform |
| `billing.view` | `billing.view` | platform |
| `billing.pay` | `billing.pay` | customer |
| `kyc.review` | `kyc.review` | platform (sensitive) |
| `risk.review` (platform) | `risk.review` | platform (sensitive) |
| `risk.review` (agency) | `risk.view` | platform |
| `risk.verify` | `risk.verify` | customer |
| `payout.approve` | `payout.approve` | platform (sensitive) |
| `payout.request` | `payout.request` | agency |
| `wallet.adjust` | `wallet.adjust` | platform (sensitive) |
| `wallet.view` | `wallet.view` | agency |
| `commission.edit` | `commission.edit` | platform (sensitive) |
| `impersonation.use` | `impersonation.use` | platform (sensitive) |
| `knowledge.view` | `knowledge.view` | agency / customer |
| `audit.view` | `audit.view` | platform |
| *(new)* | `role.view`, `role.create`, `role.update`, `role.delete` | platform |
| *(new)* | `permission.view`, `permission.create`, `permission.update`, `permission.sync` | platform |

### 3. Role model (new)

`identity_roles` stores `(slug, namespace, display_name, is_system)`.  
`identity_role_permissions` is the pivot.

System roles are seeded by `seed_system_roles` management command and `ensure_rbac_seeded()` helper. Sync is **additive only** — no existing permissions are deleted.

### 4. Membership / Invitation FK

`Membership.role_id` and `Invitation.role_id` are FKs to `identity_roles`. The `role` CharField is removed. `MembershipRecord.role` (slug string) is preserved in the port layer for backward compatibility. API still accepts `role` as slug; repositories resolve to FK on write.

### 5. super_admin bypass

`super_admin` holds **no** role-permission rows. `AuthContext.is_super_admin` property returns `True` iff `membership.role == "super_admin"`. All permission checks in `auth.py` helpers short-circuit on `is_super_admin`.

### 6. Sensitive permissions

The following codes are flagged `is_sensitive=True` and are platform-only unless noted:  
`payout.approve`, `wallet.adjust`, `commission.edit`, `impersonation.use`, `kyc.review`, `risk.review` (platform), `recording.hold` (agency).

Sensitive permissions may not be attached to agency or customer roles by the seed command (except `recording.hold` for `agency_owner`).

### 7. Namespace isolation

A permission with `namespace=agency` cannot be assigned to a platform or customer role. Enforced at seed time and at application layer in `assert_role_matches_principal`.

---

## Rollback

1. Revert migration `0002_dynamic_rbac` (drops new tables, re-adds `role` CharField).
2. Revert `domain/roles.py` to static `ROLE_PERMISSIONS` dict.
3. Revert `api/auth.py` to static `permissions_for_role` call.
4. No data loss: old `Membership.role` (slug) was the only role reference; re-added by migration rollback.

---

## Consequences

- Permission checks now require the RBAC tables to be seeded; `ensure_rbac_seeded()` is idempotent and called from `conftest.py` autouse fixture.
- API response from `session` and `login` gains `is_super_admin` and `role` object fields.
- Phase 4 views can use `require_platform_perm`, `require_agency_perm`, `require_customer_perm` helpers from `api/auth.py`.
- Custom roles (Phase 5+) require no code changes — only DB rows.
