from __future__ import annotations

from django.urls import path

from control_plane.risk.api.views import (
    AgencyCustomerAgentCollectionView,
    AgencyCustomerRiskOverrideView,
    AgencyCustomerRiskView,
    CustomerAgentCollectionView,
    CustomerRiskView,
    CustomerVerificationView,
    PlatformRiskCaseCollectionView,
    PlatformRiskOverrideView,
)

urlpatterns = [
    path(
        "platform/risk/cases",
        PlatformRiskCaseCollectionView.as_view(),
        name="platform-risk-cases",
    ),
    path(
        "platform/risk/cases/<str:case_id>/override",
        PlatformRiskOverrideView.as_view(),
        name="platform-risk-override",
    ),
    path(
        "agency/customers/<str:customer_id>/risk",
        AgencyCustomerRiskView.as_view(),
        name="agency-customer-risk",
    ),
    path(
        "agency/customers/<str:customer_id>/risk/override",
        AgencyCustomerRiskOverrideView.as_view(),
        name="agency-customer-risk-override",
    ),
    path(
        "agency/customers/<str:customer_id>/agents",
        AgencyCustomerAgentCollectionView.as_view(),
        name="agency-customer-agents",
    ),
    path("customer/risk", CustomerRiskView.as_view(), name="customer-risk"),
    path(
        "customer/verification",
        CustomerVerificationView.as_view(),
        name="customer-verification",
    ),
    path("customer/agents", CustomerAgentCollectionView.as_view(), name="customer-agents"),
]
