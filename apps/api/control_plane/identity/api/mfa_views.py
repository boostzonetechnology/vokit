"""MFA HTTP endpoints (enroll / challenge / disable / admin reset)."""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.identity.api.auth import (
    parse_uuid,
    require_auth,
    require_platform_perm,
    session_payload,
)
from control_plane.identity.api.views import CsrfAPIView, _client_ip
from control_plane.identity.infrastructure.container import mfa_service, session_gateway
from control_plane.identity.infrastructure.rate_limit import (
    mfa_send_limiter,
    mfa_verify_limiter,
)
from control_plane.platform_settings.infrastructure.container import platform_settings
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success


def _optional_uuid(value: object, *, field: str):
    if value in (None, ""):
        return None
    return parse_uuid(value, field=field)


def _rate_key(request: Request, *parts: object) -> str:
    joined = ":".join(str(p)[:128] for p in parts if p is not None and str(p) != "")
    return f"{_client_ip(request)}:{joined}"[:200]


class MfaMethodsView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_auth(request)
        return success({"methods": mfa_service().list_methods(context.user.id)})


class MfaTotpEnrollView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_auth(request)
        result = mfa_service().enroll_totp(context.user)
        return success(
            {
                "method_id": str(result.method_id),
                "otpauth_uri": result.otpauth_uri,
                "secret": result.secret,
            },
            status=201,
        )


class MfaTotpConfirmView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_auth(request)
        key = _rate_key(request, "totp_confirm", context.user.id)
        limiter = mfa_verify_limiter()
        limiter.assert_allowed(key)
        try:
            result = mfa_service().confirm_totp(
                context.user,
                method_id=parse_uuid(request.data.get("method_id"), field="method_id"),
                code=str(request.data.get("code") or ""),
            )
        except DomainError as exc:
            if exc.code == "mfa_invalid_code":
                limiter.register_failure(key)
            raise
        limiter.reset(key)
        payload: dict[str, object] = {
            "method_id": str(result.method_id),
            "type": result.method_type,
            "status": "active",
        }
        if result.recovery_codes:
            payload["recovery_codes"] = list(result.recovery_codes)
        return success(payload)


class MfaEmailEnrollView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_auth(request)
        mfa_send_limiter().assert_and_consume(_rate_key(request, "email_enroll", context.user.id))
        return success(mfa_service().enroll_email(context.user), status=201)


class MfaEmailConfirmView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_auth(request)
        key = _rate_key(request, "email_confirm", context.user.id)
        limiter = mfa_verify_limiter()
        limiter.assert_allowed(key)
        try:
            result = mfa_service().confirm_email(
                context.user,
                method_id=parse_uuid(request.data.get("method_id"), field="method_id"),
                challenge_token=str(request.data.get("challenge_token") or ""),
                code=str(request.data.get("code") or ""),
            )
        except DomainError as exc:
            if exc.code in {"mfa_invalid_code", "mfa_challenge_invalid", "mfa_challenge_locked"}:
                limiter.register_failure(key)
            raise
        limiter.reset(key)
        payload: dict[str, object] = {
            "method_id": str(result.method_id),
            "type": result.method_type,
            "status": "active",
        }
        if result.recovery_codes:
            payload["recovery_codes"] = list(result.recovery_codes)
        return success(payload)


class MfaMethodDisableView(CsrfAPIView):
    def post(self, request: Request, method_id: str) -> Response:
        context = require_auth(request)
        result = mfa_service().disable_method(
            context.user,
            context.membership,
            method_id=parse_uuid(method_id, field="method_id"),
            privileged_required=platform_settings().mfa_required_privileged(),
            code=str(request.data.get("code") or "") or None,
            recovery_code=str(request.data.get("recovery_code") or "") or None,
            method_for_code=_optional_uuid(
                request.data.get("verify_method_id"), field="verify_method_id"
            ),
        )
        return success(result)


class MfaRecoveryRegenerateView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_auth(request)
        codes = mfa_service().regenerate_recovery_codes(
            context.user,
            context.membership,
            code=str(request.data.get("code") or "") or None,
            recovery_code=str(request.data.get("recovery_code") or "") or None,
            method_id=_optional_uuid(request.data.get("method_id"), field="method_id"),
        )
        return success({"recovery_codes": list(codes)})


class MfaChallengeSendView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        token = str(request.data.get("challenge_token") or "")
        mfa_send_limiter().assert_and_consume(_rate_key(request, "challenge_send", token[:32]))
        return success(
            mfa_service().send_login_email_otp(
                challenge_token=token,
                method_id=parse_uuid(request.data.get("method_id"), field="method_id"),
            )
        )


class MfaChallengeVerifyView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        token = str(request.data.get("challenge_token") or "")
        key = _rate_key(request, "challenge_verify", token[:32])
        limiter = mfa_verify_limiter()
        limiter.assert_allowed(key)
        try:
            result = mfa_service().verify_login(
                challenge_token=token,
                sessions=session_gateway(request._request),
                method_id=_optional_uuid(request.data.get("method_id"), field="method_id"),
                code=str(request.data.get("code") or "") or None,
                recovery_code=str(request.data.get("recovery_code") or "") or None,
            )
        except DomainError as exc:
            if exc.code in {
                "mfa_invalid_code",
                "mfa_challenge_invalid",
                "mfa_challenge_locked",
                "mfa_challenge_expired",
            }:
                limiter.register_failure(key)
            raise
        limiter.reset(key)
        return success(session_payload(result.user, result.membership))


class PlatformMfaResetView(CsrfAPIView):
    def post(self, request: Request, user_id: str) -> Response:
        context = require_platform_perm(request, "mfa.reset")
        result = mfa_service().admin_reset(
            actor=context.user,
            actor_membership=context.membership,
            target_user_id=parse_uuid(user_id, field="user_id"),
            reason=str(request.data.get("reason") or ""),
        )
        return success(result)
