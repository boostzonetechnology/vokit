from __future__ import annotations

from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from control_plane.identity.api.auth import (
    parse_optional_uuid,
    parse_uuid,
    require_auth,
    require_principal,
    session_payload,
)
from control_plane.identity.application.accept_invitation import AcceptInvitationCommand
from control_plane.identity.application.authenticate import AuthenticateCommand
from control_plane.identity.application.disable_user import DisableUserCommand
from control_plane.identity.application.invite_user import InviteUserCommand
from control_plane.identity.application.logout_user import LogoutUser
from control_plane.identity.domain.policies import MembershipBinding
from control_plane.identity.domain.types import PrincipalType
from control_plane.identity.infrastructure.container import (
    accept_invitation,
    authenticate_user,
    disable_user,
    invitations,
    invite_user,
    memberships,
    session_gateway,
    users,
)
from control_plane.notifications.application.hooks import deliver_invitation
from control_plane.platform_settings.infrastructure.container import platform_settings
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success


class CsrfAPIView(APIView):
    """Session auth plus Django CSRF. DRF must not wipe request.user."""

    authentication_classes = [SessionAuthentication]
    permission_classes: list = []

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        view.csrf_exempt = False
        return view


def _client_ip(request: Request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.META.get("REMOTE_ADDR") or "unknown")[:64]


def _membership_item(user_email: str, membership) -> dict[str, object]:
    return {
        "id": str(membership.user_id),
        "membership_id": str(membership.id),
        "email": user_email,
        "principal_type": membership.principal_type.value,
        "role": membership.role,
        "tenant_id": str(membership.tenant_id) if membership.tenant_id else None,
        "customer_id": str(membership.customer_id) if membership.customer_id else None,
        "status": membership.status.value,
    }


def _invitation_item(
    invitation, *, include_token: bool = False, token: str | None = None
) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": str(invitation.id),
        "email": invitation.email,
        "principal_type": invitation.principal_type.value,
        "role": invitation.role,
        "tenant_id": str(invitation.tenant_id) if invitation.tenant_id else None,
        "customer_id": str(invitation.customer_id) if invitation.customer_id else None,
        "status": invitation.status.value,
        "expires_at": invitation.expires_at.isoformat(),
    }
    if include_token and token:
        payload["token"] = token
    return payload


def _optional_scope_id(request: Request, field: str):
    return parse_optional_uuid(request.data.get(field), field=field)


class CsrfView(CsrfAPIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request: Request) -> Response:
        return success({"csrf_token": get_token(request)})


class LoginView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        email = str(request.data.get("email") or "")
        password = str(request.data.get("password") or "")
        rate_key = f"{_client_ip(request)}:{email.strip().lower()[:128]}"
        user, membership = authenticate_user(request._request).execute(
            AuthenticateCommand(
                email=email,
                password=password,
                rate_key=rate_key,
                privileged_mfa_required=platform_settings().mfa_required_privileged(),
            )
        )
        return success(session_payload(user, membership))


class LogoutView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        require_auth(request)
        LogoutUser(session_gateway(request._request)).execute()
        return success({"logged_out": True})


class SessionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_auth(request)
        return success(session_payload(context.user, context.membership))


class AcceptInvitationView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        token = str(request.data.get("token") or "")
        password = str(request.data.get("password") or "")
        user = accept_invitation().execute(AcceptInvitationCommand(token=token, password=password))
        return success({"user_id": str(user.id), "email": user.email}, status=201)


class MeView(CsrfAPIView):
    principal_type: PrincipalType = PrincipalType.PLATFORM

    def get(self, request: Request) -> Response:
        context = require_principal(request, self.principal_type)
        return success(session_payload(context.user, context.membership))


class TeamListView(CsrfAPIView):
    principal_type: PrincipalType = PrincipalType.PLATFORM

    def get(self, request: Request) -> Response:
        context = require_principal(request, self.principal_type)
        rows = memberships().list_for_scope(
            principal_type=self.principal_type,
            tenant_id=context.membership.tenant_id,
            customer_id=context.membership.customer_id,
        )
        emails = {
            item.id: item.email for item in users().list_by_ids([row.user_id for row in rows])
        }
        return success([_membership_item(emails.get(row.user_id, ""), row) for row in rows])

    def post(self, request: Request) -> Response:
        context = require_principal(request, self.principal_type)
        binding = self._binding_from_session(context, request)
        record, token = invite_user().execute(
            InviteUserCommand(
                email=str(request.data.get("email") or ""),
                binding=binding,
                invited_by_id=context.user.id,
                actor_membership=context.membership,
            )
        )
        deliver_invitation(
            email=record.email,
            role=record.role,
            principal_type=record.principal_type,
            tenant_id=record.tenant_id,
            customer_id=record.customer_id,
            token=token,
            actor_id=context.user.id,
            actor_role=context.membership.role,
        )
        return success(_invitation_item(record, include_token=True, token=token), status=201)

    def _binding_from_session(self, context, request: Request) -> MembershipBinding:
        if self.principal_type is PrincipalType.PLATFORM:
            try:
                principal = PrincipalType(str(request.data.get("principal_type") or ""))
            except ValueError as exc:
                raise DomainError("validation_error", "principal_type is invalid.") from exc
            return MembershipBinding(
                principal_type=principal,
                role=str(request.data.get("role") or ""),
                tenant_id=_optional_scope_id(request, "tenant_id"),
                customer_id=_optional_scope_id(request, "customer_id"),
            )
        if self.principal_type is PrincipalType.AGENCY:
            customer_id = _optional_scope_id(request, "customer_id")
            principal = PrincipalType.CUSTOMER if customer_id else PrincipalType.AGENCY
            return MembershipBinding(
                principal_type=principal,
                role=str(request.data.get("role") or ""),
                tenant_id=context.membership.tenant_id,
                customer_id=customer_id,
            )
        return MembershipBinding(
            principal_type=PrincipalType.CUSTOMER,
            role=str(request.data.get("role") or ""),
            tenant_id=context.membership.tenant_id,
            customer_id=context.membership.customer_id,
        )


class InvitationListView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.PLATFORM)
        rows = invitations().list_for_scope(
            principal_type=PrincipalType.PLATFORM,
            tenant_id=context.membership.tenant_id,
            customer_id=context.membership.customer_id,
        )
        return success([_invitation_item(row) for row in rows])

    def post(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.PLATFORM)
        try:
            principal = PrincipalType(str(request.data.get("principal_type") or ""))
        except ValueError as exc:
            raise DomainError("validation_error", "principal_type is invalid.") from exc
        record, token = invite_user().execute(
            InviteUserCommand(
                email=str(request.data.get("email") or ""),
                binding=MembershipBinding(
                    principal_type=principal,
                    role=str(request.data.get("role") or ""),
                    tenant_id=_optional_scope_id(request, "tenant_id"),
                    customer_id=_optional_scope_id(request, "customer_id"),
                ),
                invited_by_id=context.user.id,
                actor_membership=context.membership,
            )
        )
        deliver_invitation(
            email=record.email,
            role=record.role,
            principal_type=record.principal_type,
            tenant_id=record.tenant_id,
            customer_id=record.customer_id,
            token=token,
            actor_id=context.user.id,
            actor_role=context.membership.role,
        )
        return success(_invitation_item(record, include_token=True, token=token), status=201)


class DisableUserView(CsrfAPIView):
    principal_type: PrincipalType = PrincipalType.PLATFORM

    def post(self, request: Request, user_id: str) -> Response:
        context = require_principal(request, self.principal_type)
        revoked = disable_user(request._request).execute(
            DisableUserCommand(
                actor_id=context.user.id,
                actor_membership=context.membership,
                target_user_id=parse_uuid(user_id, field="user_id"),
            )
        )
        return success({"disabled_user_id": user_id, "sessions_revoked": revoked})
