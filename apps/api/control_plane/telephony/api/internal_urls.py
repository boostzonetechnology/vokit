from __future__ import annotations

from django.urls import path

from control_plane.telephony.api.internal import (
    DidResolveView,
    ToolInvokeView,
    TrainingBootstrapView,
    TrainingConfirmView,
    TrainingEndView,
    TrainingProposeView,
    VoiceSessionBootstrapView,
    VoiceSessionContinueView,
    VoiceSessionEndView,
    VoiceSessionEventsView,
    VoiceSessionTransferStatusView,
    VoiceSessionTransferView,
    VoiceSessionVoicemailView,
)

urlpatterns = [
    path("did/resolve/", DidResolveView.as_view(), name="telephony-did-resolve"),
    path("did-resolve/", DidResolveView.as_view(), name="telephony-did-resolve-legacy"),
    path(
        "voice-session/bootstrap/",
        VoiceSessionBootstrapView.as_view(),
        name="telephony-bootstrap",
    ),
    path(
        "voice-session/events/",
        VoiceSessionEventsView.as_view(),
        name="telephony-events",
    ),
    path("voice-session/end/", VoiceSessionEndView.as_view(), name="telephony-end"),
    path(
        "voice-session/continue/",
        VoiceSessionContinueView.as_view(),
        name="telephony-continue",
    ),
    path(
        "voice-session/transfer/",
        VoiceSessionTransferView.as_view(),
        name="telephony-transfer",
    ),
    path(
        "voice-session/transfer/status/",
        VoiceSessionTransferStatusView.as_view(),
        name="telephony-transfer-status",
    ),
    path(
        "voice-session/voicemail/",
        VoiceSessionVoicemailView.as_view(),
        name="telephony-voicemail",
    ),
    path("tools/invoke/", ToolInvokeView.as_view(), name="telephony-tools-invoke"),
    path(
        "training-session/bootstrap/",
        TrainingBootstrapView.as_view(),
        name="telephony-training-bootstrap",
    ),
    path(
        "training-session/propose/",
        TrainingProposeView.as_view(),
        name="telephony-training-propose",
    ),
    path(
        "training-session/confirm/",
        TrainingConfirmView.as_view(),
        name="telephony-training-confirm",
    ),
    path(
        "training-session/end/",
        TrainingEndView.as_view(),
        name="telephony-training-end",
    ),
]
