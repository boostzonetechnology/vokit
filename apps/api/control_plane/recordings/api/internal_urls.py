from __future__ import annotations

from django.urls import path

from control_plane.recordings.api.internal import (
    RecordingAccessValidateView,
    RecordingIngestView,
)

urlpatterns = [
    path("ingest/", RecordingIngestView.as_view(), name="recordings-ingest"),
    path(
        "access/validate/",
        RecordingAccessValidateView.as_view(),
        name="recordings-access-validate",
    ),
]
