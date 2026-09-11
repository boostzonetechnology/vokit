from __future__ import annotations

from django.urls import path

from control_plane.tenancy.api.agency_views import (
    AgencyCapabilitiesView,
    AgencyCollectionView,
    AgencyCommissionView,
    AgencyDetailView,
    AgencyFinanceView,
    AgencyNotesView,
    AgencyReassignCustomerView,
    AgencyStatusView,
)
from control_plane.tenancy.api.views import (
    AgencyIsolationRecordDetailView,
    AgencyIsolationRecordView,
    TenantCollectionView,
    TenantDetailView,
    TenantMigrationBatchView,
    TenantMigrationView,
    TenantProvisionRetryView,
)

urlpatterns = [
    path("platform/agencies", AgencyCollectionView.as_view(), name="platform-agencies"),
    path(
        "platform/agencies/<str:agency_id>",
        AgencyDetailView.as_view(),
        name="platform-agency-detail",
    ),
    path(
        "platform/agencies/<str:agency_id>/status",
        AgencyStatusView.as_view(),
        name="platform-agency-status",
    ),
    path(
        "platform/agencies/<str:agency_id>/capabilities",
        AgencyCapabilitiesView.as_view(),
        name="platform-agency-capabilities",
    ),
    path(
        "platform/agencies/<str:agency_id>/commission",
        AgencyCommissionView.as_view(),
        name="platform-agency-commission",
    ),
    path(
        "platform/agencies/<str:agency_id>/finance",
        AgencyFinanceView.as_view(),
        name="platform-agency-finance",
    ),
    path(
        "platform/agencies/<str:agency_id>/notes",
        AgencyNotesView.as_view(),
        name="platform-agency-notes",
    ),
    path(
        "platform/agencies/<str:agency_id>/reassign-customer",
        AgencyReassignCustomerView.as_view(),
        name="platform-agency-reassign",
    ),
    path("platform/tenants", TenantCollectionView.as_view(), name="platform-tenants"),
    path(
        "platform/tenants/migrations",
        TenantMigrationBatchView.as_view(),
        name="platform-tenant-migrations",
    ),
    path(
        "platform/tenants/<str:tenant_id>",
        TenantDetailView.as_view(),
        name="platform-tenant-detail",
    ),
    path(
        "platform/tenants/<str:tenant_id>/provision/retry",
        TenantProvisionRetryView.as_view(),
        name="platform-tenant-provision-retry",
    ),
    path(
        "platform/tenants/<str:tenant_id>/migrations",
        TenantMigrationView.as_view(),
        name="platform-tenant-migration",
    ),
    path(
        "agency/data-plane/records",
        AgencyIsolationRecordView.as_view(),
        name="agency-data-plane-records",
    ),
    path(
        "agency/data-plane/records/<str:object_id>",
        AgencyIsolationRecordDetailView.as_view(),
        name="agency-data-plane-record",
    ),
]
