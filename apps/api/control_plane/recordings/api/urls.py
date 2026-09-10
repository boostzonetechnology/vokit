from __future__ import annotations

from django.urls import path

from control_plane.recordings.api.views import (
    AgencyCallArtifactAccessView,
    AgencyCallArtifactCollectionView,
    AgencyCallArtifactDeleteView,
    AgencyCallArtifactHoldView,
    CustomerCallArtifactAccessView,
    CustomerCallArtifactCollectionView,
    PlatformCallArtifactAccessView,
    PlatformCallArtifactCollectionView,
    PlatformCallArtifactDeleteView,
    PlatformCallArtifactHoldView,
)

urlpatterns = [
    path(
        "platform/calls/<str:call_id>/artifacts",
        PlatformCallArtifactCollectionView.as_view(),
        name="platform-call-artifacts",
    ),
    path(
        "platform/calls/<str:call_id>/artifacts/<str:artifact_id>/access",
        PlatformCallArtifactAccessView.as_view(),
        name="platform-call-artifact-access",
    ),
    path(
        "platform/calls/<str:call_id>/artifacts/<str:artifact_id>/hold",
        PlatformCallArtifactHoldView.as_view(),
        name="platform-call-artifact-hold",
    ),
    path(
        "platform/calls/<str:call_id>/artifacts/<str:artifact_id>/delete",
        PlatformCallArtifactDeleteView.as_view(),
        name="platform-call-artifact-delete",
    ),
    path(
        "agency/calls/<str:call_id>/artifacts",
        AgencyCallArtifactCollectionView.as_view(),
        name="agency-call-artifacts",
    ),
    path(
        "agency/calls/<str:call_id>/artifacts/<str:artifact_id>/access",
        AgencyCallArtifactAccessView.as_view(),
        name="agency-call-artifact-access",
    ),
    path(
        "agency/calls/<str:call_id>/artifacts/<str:artifact_id>/hold",
        AgencyCallArtifactHoldView.as_view(),
        name="agency-call-artifact-hold",
    ),
    path(
        "agency/calls/<str:call_id>/artifacts/<str:artifact_id>/delete",
        AgencyCallArtifactDeleteView.as_view(),
        name="agency-call-artifact-delete",
    ),
    path(
        "customer/calls/<str:call_id>/artifacts",
        CustomerCallArtifactCollectionView.as_view(),
        name="customer-call-artifacts",
    ),
    path(
        "customer/calls/<str:call_id>/artifacts/<str:artifact_id>/access",
        CustomerCallArtifactAccessView.as_view(),
        name="customer-call-artifact-access",
    ),
]
