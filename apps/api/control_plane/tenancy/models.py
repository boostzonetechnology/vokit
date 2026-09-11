from __future__ import annotations

from django.db import models

from shared_kernel.ids import new_uuid7


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    display_name = models.CharField(max_length=255)
    status = models.CharField(max_length=32, default="provisioning")
    agency_status = models.CharField(max_length=32, default="pending")
    legal_name = models.CharField(max_length=255, blank=True, default="")
    currency = models.CharField(max_length=3, default="USD")
    commission_rate_bps = models.PositiveIntegerField(default=0)
    rate_effective_at = models.DateTimeField(null=True, blank=True)
    can_create_customers = models.BooleanField(default=True)
    can_create_agents = models.BooleanField(default=True)
    can_purchase_numbers = models.BooleanField(default=True)
    can_request_payouts = models.BooleanField(default=True)
    existing_customer_services = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenants"


class TenantDatabase(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="database"
    )
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField(default=3306)
    name = models.CharField(max_length=64)
    db_username = models.CharField(max_length=128, blank=True, default="")
    secret_ref = models.CharField(max_length=128)
    tls_required = models.BooleanField(default=False)
    status = models.CharField(max_length=32, default="allocating")
    schema_version = models.CharField(max_length=64, default="")
    last_health_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenant_databases"


class TenantProvisioningJob(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="provisioning_jobs"
    )
    step = models.CharField(max_length=32, default="created")
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenant_provisioning_jobs"


class TenantMigrationJob(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="migration_jobs"
    )
    source_version = models.CharField(max_length=64, blank=True, default="")
    target_version = models.CharField(max_length=64)
    status = models.CharField(max_length=32, default="pending")
    canary = models.BooleanField(default=False)
    last_error = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenant_migration_jobs"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant"],
                condition=models.Q(status__in=["pending", "locked", "running"]),
                name="tenancy_one_active_migration",
            )
        ]


class AgencyNote(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="notes"
    )
    body = models.TextField(max_length=2000)
    risk_flag = models.BooleanField(default=False)
    created_by_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agency_notes"
        indexes = [
            models.Index(fields=["tenant", "-created_at"], name="idx_agency_notes_tenant"),
        ]


class TenantDbCredential(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    database = models.OneToOneField(
        TenantDatabase,
        on_delete=models.CASCADE,
        related_name="credential",
    )
    ciphertext = models.CharField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenant_db_credentials"
