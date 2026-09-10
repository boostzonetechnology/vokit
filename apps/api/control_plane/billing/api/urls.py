from __future__ import annotations

from django.urls import path

from control_plane.billing.api.views import (
    AgencyCustomerInvoiceCollectionView,
    AgencyCustomerSubscriptionView,
    AgencyPlanCollectionView,
    CustomerInvoiceCollectionView,
    CustomerInvoicePayView,
    CustomerPaymentMethodCollectionView,
    CustomerTopUpView,
    CustomerUsageView,
    PlatformCustomerSubscriptionView,
    PlatformDisputeCollectionView,
    PlatformInvoiceCollectionView,
    PlatformPaymentCollectionView,
    PlatformPlanArchiveView,
    PlatformPlanCollectionView,
    PlatformPlanVersionDetailView,
    PlatformPlanVersionView,
)

urlpatterns = [
    path("platform/plans", PlatformPlanCollectionView.as_view(), name="platform-plans"),
    path(
        "platform/plans/<str:plan_id>/versions",
        PlatformPlanVersionView.as_view(),
        name="platform-plan-versions",
    ),
    path(
        "platform/plans/<str:plan_id>/archive",
        PlatformPlanArchiveView.as_view(),
        name="platform-plan-archive",
    ),
    path(
        "platform/plan-versions/<str:version_id>",
        PlatformPlanVersionDetailView.as_view(),
        name="platform-plan-version",
    ),
    path(
        "platform/customers/<str:customer_id>/subscription",
        PlatformCustomerSubscriptionView.as_view(),
        name="platform-customer-subscription",
    ),
    path("platform/invoices", PlatformInvoiceCollectionView.as_view(), name="platform-invoices"),
    path("platform/payments", PlatformPaymentCollectionView.as_view(), name="platform-payments"),
    path("platform/disputes", PlatformDisputeCollectionView.as_view(), name="platform-disputes"),
    path("agency/plans", AgencyPlanCollectionView.as_view(), name="agency-plans"),
    path(
        "agency/customers/<str:customer_id>/subscription",
        AgencyCustomerSubscriptionView.as_view(),
        name="agency-customer-subscription",
    ),
    path(
        "agency/customer-invoices",
        AgencyCustomerInvoiceCollectionView.as_view(),
        name="agency-customer-invoices",
    ),
    path("customer/invoices", CustomerInvoiceCollectionView.as_view(), name="customer-invoices"),
    path(
        "customer/invoices/<str:invoice_id>/pay",
        CustomerInvoicePayView.as_view(),
        name="customer-invoice-pay",
    ),
    path("customer/usage", CustomerUsageView.as_view(), name="customer-usage"),
    path("customer/usage/top-ups", CustomerTopUpView.as_view(), name="customer-topups"),
    path(
        "customer/payment-methods",
        CustomerPaymentMethodCollectionView.as_view(),
        name="customer-payment-methods",
    ),
]
