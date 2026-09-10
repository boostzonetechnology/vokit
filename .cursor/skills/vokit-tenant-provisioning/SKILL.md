# Vokit Tenant Provisioning Skill

## Use when
Use when creating, activating, suspending, moving, restoring or closing a tenant.

## Workflow
- create control-plane tenant;
- allocate database identity;
- generate/store credential reference;
- establish remote MySQL connectivity;
- bootstrap schema;
- verify schema version;
- create initial platform/tenant configuration;
- mark tenant ready;
- emit tenant.provisioned event;
- audit every stage.

## Saga requirements
Provisioning must be resumable and idempotent. Every step needs a persisted state, retry path, timeout, compensation or manual intervention state.
Never mark a tenant Active while the tenant DB is unverified.
