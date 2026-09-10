from __future__ import annotations

import hmac

from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from control_plane.telephony.infrastructure.container import voice_control
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success


def _require_internal(request: Request) -> None:
    expected = str(getattr(settings, "VOKIT_INTERNAL_TELEPHONY_TOKEN", "") or "")
    provided = str(request.headers.get("X-Vokit-Internal-Token") or "")
    if not expected or not hmac.compare_digest(expected, provided):
        raise DomainError("unauthenticated", "Authentication required.", http_status=401)


class InternalTelephonyView(APIView):
    authentication_classes: list = []
    permission_classes: list = []


class DidResolveView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        return success(voice_control().resolve_did(str(data.get("did") or "")))


class VoiceSessionBootstrapView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            voice_control().bootstrap(
                did=str(data.get("did") or ""),
                edge_call_id=str(data.get("edge_call_id") or ""),
                from_number=str(data.get("from_number") or ""),
                sip_call_id=str(data.get("sip_call_id") or ""),
                direction=str(data.get("direction") or "inbound"),
            )
        )


class VoiceSessionEventsView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            voice_control().record_event(
                edge_call_id=str(data.get("edge_call_id") or ""),
                event_type=str(data.get("event_type") or ""),
                role=str(data.get("role") or ""),
                reason=str(data.get("reason") or ""),
            )
        )


class VoiceSessionEndView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            voice_control().end_session(
                edge_call_id=str(data.get("edge_call_id") or ""),
                reason=str(data.get("reason") or ""),
                status=str(data.get("status") or ""),
            )
        )


class VoiceSessionContinueView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        elapsed = data.get("elapsed_seconds", 0)
        if type(elapsed) is not int:
            raise DomainError("validation_error", "elapsed_seconds must be an integer.")
        return success(
            voice_control().continue_session(
                edge_call_id=str(data.get("edge_call_id") or ""),
                elapsed_seconds=elapsed,
            )
        )


class VoiceSessionTransferView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            voice_control().request_transfer(
                edge_call_id=str(data.get("edge_call_id") or ""),
                destination_id=str(data.get("destination_id") or ""),
            )
        )


class VoiceSessionTransferStatusView(InternalTelephonyView):
    def get(self, request: Request) -> Response:
        _require_internal(request)
        return success(
            voice_control().transfer_status(
                edge_call_id=str(request.query_params.get("edge_call_id") or "")
            )
        )


class ToolInvokeView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        arguments = data.get("arguments")
        return success(
            voice_control().invoke_tool(
                edge_call_id=str(data.get("edge_call_id") or ""),
                tool=str(data.get("tool") or ""),
                arguments=arguments if isinstance(arguments, dict) else {},
            )
        )


class VoiceSessionVoicemailView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        duration = data.get("duration_seconds", 0)
        if type(duration) is not int:
            raise DomainError("validation_error", "duration_seconds must be an integer.")
        return success(
            voice_control().record_voicemail(
                edge_call_id=str(data.get("edge_call_id") or ""),
                direction=str(data.get("direction") or "inbound"),
                action=str(data.get("action") or "start"),
                duration_seconds=duration,
            )
        )


class TrainingBootstrapView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            voice_control().training_bootstrap(
                session_token=str(data.get("session_token") or "")
            )
        )


class TrainingProposeView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            voice_control().training_propose(
                session_token=str(data.get("session_token") or ""),
                kind=str(data.get("kind") or ""),
                name=str(data.get("name") or ""),
                body=str(data.get("body") or ""),
                scope=str(data.get("scope") or ""),
            )
        )


class TrainingConfirmView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            voice_control().training_confirm(
                session_token=str(data.get("session_token") or "")
            )
        )


class TrainingEndView(InternalTelephonyView):
    def post(self, request: Request) -> Response:
        _require_internal(request)
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            voice_control().training_end(session_token=str(data.get("session_token") or ""))
        )
