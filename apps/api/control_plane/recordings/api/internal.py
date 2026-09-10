from __future__ import annotations

import hmac

from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from control_plane.recordings.application.service import IngestCommand
from control_plane.recordings.infrastructure.container import recording_control
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success


def _require_recording_internal(request: Request) -> None:
    expected = str(getattr(settings, "VOKIT_INTERNAL_RECORDING_TOKEN", "") or "")
    provided = str(request.headers.get("X-Vokit-Internal-Token") or "")
    if not expected or not hmac.compare_digest(expected, provided):
        raise DomainError("unauthenticated", "Authentication required.", http_status=401)


class InternalRecordingView(APIView):
    authentication_classes: list = []
    permission_classes: list = []


class RecordingIngestView(InternalRecordingView):
    def post(self, request: Request) -> Response:
        _require_recording_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            recording_control().ingest(
                IngestCommand(
                    event_id=str(data.get("event_id") or ""),
                    edge_call_id=str(data.get("edge_call_id") or ""),
                    call_id=str(data.get("call_id") or ""),
                    artifact_id=str(data.get("artifact_id") or ""),
                    kind=str(data.get("kind") or "call_recording"),
                    content_type=str(data.get("content_type") or ""),
                    size_bytes=data.get("size_bytes", 0),
                    checksum=str(data.get("checksum") or ""),
                    provider_ref=str(data.get("provider_ref") or ""),
                    tenant_id=str(data.get("tenant_id") or ""),
                )
            )
        )


class RecordingAccessValidateView(InternalRecordingView):
    def post(self, request: Request) -> Response:
        _require_recording_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        return success(recording_control().validate_access(str(data.get("token") or "")))
