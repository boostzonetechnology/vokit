from __future__ import annotations

from django.urls import path

from control_plane.audit.api.views import (
    PlatformAuditCollectionView,
    PlatformAuditMutationView,
)

urlpatterns = [
    path(
        "platform/audit-events",
        PlatformAuditCollectionView.as_view(),
        name="platform-audit-events",
    ),
    path(
        "platform/audit-events/<str:event_id>",
        PlatformAuditMutationView.as_view(),
        name="platform-audit-event",
    ),
]
