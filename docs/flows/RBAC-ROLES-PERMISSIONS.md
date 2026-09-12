# Flow: Roles, permissions, and RBAC (ADR-007)

**Status:** Implemented (backend)  
**Surface:** Django API (`/api/v1/platform/roles`, `/permissions`, agency/customer `/roles`)  
**Related:** SRS SA18-001..003, RBAC-001..006, SEC-002, VKT-008, ADR-007  
**Frontend:** Not wired yet — this doc is the FE integration contract.

---

## Model

```text
Permission (catalog)  ←── RolePermission ──→  Role
                                              ↑
                                         Membership.role_id
                                              ↑
                                            User
```

- One membership per user (Q-001): platform XOR agency XOR customer.
- One role per membership.
- Permission codes: `{module}.{action}` (CRUD + sensitive actions). Unique per `(namespace, code)`.
- Namespaces: `platform` | `agency` | `customer` (never mixed on a role).

### Super Admin bypass

Role slug `super_admin` + platform principal → **all permission checks pass**.  
Session returns `permissions: []` and `is_super_admin: true`.  
No pivot rows required. Other roles must have explicit permissions.

---

## Session /me payload (additive)

```json
{
  "user": { "id": "...", "email": "...", "status": "active" },
  "membership": {
    "id": "...",
    "principal_type": "platform|agency|customer",
    "role": "agency_owner",
    "tenant_id": "...|null",
    "customer_id": "...|null",
    "status": "active"
  },
  "role": { "id": "...", "slug": "agency_owner", "namespace": "agency" },
  "permissions": ["customer.view", "customer.create", "..."],
  "is_super_admin": false
}
```

`membership.role` remains the **slug** for backward compatibility.

---

## APIs

### Permissions (platform)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/platform/permissions?namespace=&module=` | `permission.view` |
| POST | `/api/v1/platform/permissions` | `permission.create` (custom) |
| POST | `/api/v1/platform/permissions/sync` | `permission.sync` |

Sync is **additive only** (insert missing catalog codes; never delete).

Also: `python manage.py sync_permissions` then `python manage.py seed_system_roles`  
(or `ensure_rbac_seeded()` which does both).

### Roles (platform admin — SA18)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/platform/roles?namespace=` | `role.view` |
| POST | `/api/v1/platform/roles` | `role.create` (platform namespace only in V1) |
| GET | `/api/v1/platform/roles/{id}` | `role.view` |
| PATCH | `/api/v1/platform/roles/{id}` | `role.update` (display_name + permissions replace) |
| DELETE | `/api/v1/platform/roles/{id}` | `role.delete` (non-system only) |

Cannot delete system roles. Cannot modify `super_admin`.

### Role lists for invite dropdowns (read-only)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/agency/roles` | `team.view` |
| GET | `/api/v1/customer/roles` | `team.view` |

### Invite (unchanged shape)

`POST /api/v1/platform/users` | `/agency/team` | `/customer/team`

Body still uses `"role": "<slug>"` (e.g. `agency_admin`). Server resolves slug → `role_id`.

---

## System role slugs (stable)

| Namespace | Slugs |
|---|---|
| platform | `super_admin`, `finance_admin`, `compliance_kyc`, `support_admin` |
| agency | `agency_owner`, `agency_admin`, `agency_agent_builder`, `agency_finance` |
| customer | `customer_owner`, `customer_admin`, `customer_analyst` |

Keep these slugs so current invite UIs keep working before FE refactor.

---

## FE integration checklist (later)

1. Stop hardcoding `PLATFORM_ROLES` / `PLATFORM_ROLE_PERMISSIONS` in web-ui.
2. Load roles from `GET /platform/roles` (or agency/customer `/roles` for invites).
3. Load permissions from `GET /platform/permissions` for role editor.
4. Use `is_super_admin` for UI chrome only — **never** as a security boundary (WF-08).
5. Hide/disable actions using `permissions[]` for UX only; server 403 remains authoritative.
6. Role create/edit UI: platform portal only for V1.

---

## Ops bootstrap

```text
migrate
python manage.py sync_permissions   # or ensure via seed
python manage.py seed_system_roles
python manage.py bootstrap_platform_owner --email ... --password ...
```

`bootstrap_platform_owner` and demo seeds call `ensure_rbac_seeded()` first.
