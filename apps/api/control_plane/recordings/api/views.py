from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.identity.api.auth import (
    parse_uuid,
    require_agency_perm,
    require_customer_perm,
    require_platform_perm,
)
from control_plane.identity.api.views import CsrfAPIView
from control_plane.recordings.infrastructure.container import recording_control
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success


def _bool_field(data: dict, name: str, default: bool | None = None) -> bool:
    raw = data.get(name, default)
    if type(raw) is not bool:
        raise DomainError("validation_error", f"{name} must be a boolean.")
    return raw


class PlatformCallArtifactCollectionView(CsrfAPIView):
    def get(self, request: Request, call_id: str) -> Response:
        require_platform_perm(request, "recording.view")
        return success(
            recording_control().list_for_call(
                call_id=parse_uuid(call_id, field="call_id"),
                actor_tenant_id=None,
                actor_customer_id=None,
                privileged=True,
            )
        )


class PlatformCallArtifactAccessView(CsrfAPIView):
    def post(self, request: Request, call_id: str, artifact_id: str) -> Response:
        context = require_platform_perm(request, "recording.view")
        return success(
            recording_control().grant_access(
                call_id=parse_uuid(call_id, field="call_id"),
                artifact_id=parse_uuid(artifact_id, field="artifact_id"),
                actor_id=context.user.id,
                actor_tenant_id=None,
                actor_customer_id=None,
                privileged=True,
            )
        )


class PlatformCallArtifactHoldView(CsrfAPIView):
    def post(self, request: Request, call_id: str, artifact_id: str) -> Response:
        require_platform_perm(request, "recording.view")
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            recording_control().set_hold(
                call_id=parse_uuid(call_id, field="call_id"),
                artifact_id=parse_uuid(artifact_id, field="artifact_id"),
                hold=_bool_field(data, "hold"),
                actor_tenant_id=None,
                actor_customer_id=None,
                privileged=True,
            )
        )


class PlatformCallArtifactDeleteView(CsrfAPIView):
    def post(self, request: Request, call_id: str, artifact_id: str) -> Response:
        require_platform_perm(request, "recording.view")
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            recording_control().delete(
                call_id=parse_uuid(call_id, field="call_id"),
                artifact_id=parse_uuid(artifact_id, field="artifact_id"),
                confirm=_bool_field(data, "confirm", False),
                actor_tenant_id=None,
                actor_customer_id=None,
                privileged=True,
            )
        )


class AgencyCallArtifactCollectionView(CsrfAPIView):
    def get(self, request: Request, call_id: str) -> Response:
        context = require_agency_perm(request, "recording.view")
        return success(
            recording_control().list_for_call(
                call_id=parse_uuid(call_id, field="call_id"),
                actor_tenant_id=context.membership.tenant_id,
                actor_customer_id=None,
                privileged=False,
            )
        )


class AgencyCallArtifactAccessView(CsrfAPIView):
    def post(self, request: Request, call_id: str, artifact_id: str) -> Response:
        context = require_agency_perm(request, "recording.view")
        return success(
            recording_control().grant_access(
                call_id=parse_uuid(call_id, field="call_id"),
                artifact_id=parse_uuid(artifact_id, field="artifact_id"),
                actor_id=context.user.id,
                actor_tenant_id=context.membership.tenant_id,
                actor_customer_id=None,
                privileged=False,
            )
        )


class AgencyCallArtifactHoldView(CsrfAPIView):
    def post(self, request: Request, call_id: str, artifact_id: str) -> Response:
        context = require_agency_perm(request, "recording.hold")
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            recording_control().set_hold(
                call_id=parse_uuid(call_id, field="call_id"),
                artifact_id=parse_uuid(artifact_id, field="artifact_id"),
                hold=_bool_field(data, "hold"),
                actor_tenant_id=context.membership.tenant_id,
                actor_customer_id=None,
                privileged=False,
            )
        )


class AgencyCallArtifactDeleteView(CsrfAPIView):
    def post(self, request: Request, call_id: str, artifact_id: str) -> Response:
        context = require_agency_perm(request, "recording.hold")
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            recording_control().delete(
                call_id=parse_uuid(call_id, field="call_id"),
                artifact_id=parse_uuid(artifact_id, field="artifact_id"),
                confirm=_bool_field(data, "confirm", False),
                actor_tenant_id=context.membership.tenant_id,
                actor_customer_id=None,
                privileged=False,
            )
        )


class CustomerCallArtifactCollectionView(CsrfAPIView):
    def get(self, request: Request, call_id: str) -> Response:
        context = require_customer_perm(request, "recording.view")
        return success(
            recording_control().list_for_call(
                call_id=parse_uuid(call_id, field="call_id"),
                actor_tenant_id=context.membership.tenant_id,
                actor_customer_id=context.membership.customer_id,
                privileged=False,
            )
        )


class CustomerCallArtifactAccessView(CsrfAPIView):
    def post(self, request: Request, call_id: str, artifact_id: str) -> Response:
        context = require_customer_perm(request, "recording.view")
        return success(
            recording_control().grant_access(
                call_id=parse_uuid(call_id, field="call_id"),
                artifact_id=parse_uuid(artifact_id, field="artifact_id"),
                actor_id=context.user.id,
                actor_tenant_id=context.membership.tenant_id,
                actor_customer_id=context.membership.customer_id,
                privileged=False,
            )
        )
