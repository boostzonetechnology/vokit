from __future__ import annotations

from django.urls import path

from control_plane.customers.api.views import (
    AgencyCustomerCollectionView,
    AgencyCustomerDetailView,
    AgencyCustomerStatusView,
    CustomerAccountView,
    PlatformBanKeyView,
    PlatformCustomerCollectionView,
    PlatformCustomerDetailView,
    PlatformCustomerStatusView,
)

urlpatterns = [
    path(
        "platform/customers",
        PlatformCustomerCollectionView.as_view(),
        name="platform-customers",
    ),
    path(
        "platform/customers/<str:customer_id>",
        PlatformCustomerDetailView.as_view(),
        name="platform-customer-detail",
    ),
    path(
        "platform/customers/<str:customer_id>/status",
        PlatformCustomerStatusView.as_view(),
        name="platform-customer-status",
    ),
    path(
        "platform/risk/ban-keys",
        PlatformBanKeyView.as_view(),
        name="platform-ban-keys",
    ),
    path(
        "agency/customers",
        AgencyCustomerCollectionView.as_view(),
        name="agency-customers",
    ),
    path(
        "agency/customers/<str:customer_id>",
        AgencyCustomerDetailView.as_view(),
        name="agency-customer-detail",
    ),
    path(
        "agency/customers/<str:customer_id>/status",
        AgencyCustomerStatusView.as_view(),
        name="agency-customer-status",
    ),
    path(
        "customer/account",
        CustomerAccountView.as_view(),
        name="customer-account",
    ),
]
