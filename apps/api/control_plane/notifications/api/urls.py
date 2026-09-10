from __future__ import annotations

from django.urls import path

from control_plane.identity.domain.types import PrincipalType
from control_plane.notifications.api.views import (
    AgencyPreferenceView,
    CustomerPreferenceView,
    InboxReadView,
    InboxView,
    PlatformAnnouncementView,
    PlatformDeliveryCollectionView,
    PlatformTemplateCollectionView,
)

urlpatterns = [
    path(
        "platform/notification-templates",
        PlatformTemplateCollectionView.as_view(),
        name="platform-notification-templates",
    ),
    path(
        "platform/notification-deliveries",
        PlatformDeliveryCollectionView.as_view(),
        name="platform-notification-deliveries",
    ),
    path(
        "platform/announcements",
        PlatformAnnouncementView.as_view(),
        name="platform-announcements",
    ),
    path(
        "platform/notifications",
        InboxView.as_view(principal_type=PrincipalType.PLATFORM),
        name="platform-notifications",
    ),
    path(
        "platform/notifications/<str:notification_id>/read",
        InboxReadView.as_view(principal_type=PrincipalType.PLATFORM),
        name="platform-notification-read",
    ),
    path(
        "agency/notifications",
        InboxView.as_view(principal_type=PrincipalType.AGENCY),
        name="agency-notifications",
    ),
    path(
        "agency/notifications/<str:notification_id>/read",
        InboxReadView.as_view(principal_type=PrincipalType.AGENCY),
        name="agency-notification-read",
    ),
    path(
        "agency/notification-preferences",
        AgencyPreferenceView.as_view(),
        name="agency-notification-preferences",
    ),
    path(
        "customer/notifications",
        InboxView.as_view(principal_type=PrincipalType.CUSTOMER),
        name="customer-notifications",
    ),
    path(
        "customer/notifications/<str:notification_id>/read",
        InboxReadView.as_view(principal_type=PrincipalType.CUSTOMER),
        name="customer-notification-read",
    ),
    path(
        "customer/notification-preferences",
        CustomerPreferenceView.as_view(),
        name="customer-notification-preferences",
    ),
]
