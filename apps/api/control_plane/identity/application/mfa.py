"""MFA enrollment, login challenge, disable, recovery, and admin reset."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import timedelta

import pyotp

from control_plane.audit.application.record import RecordAuditCommand
from control_plane.audit.infrastructure.container import record_audit
from control_plane.identity.application.ports import (
    MembershipRecord,
    MembershipRepository,
    SessionGateway,
    UserRecord,
    UserRepository,
)
from control_plane.identity.domain.mfa import (
    LOGIN_CHALLENGE_TTL_SECONDS,
    MAX_OTP_ATTEMPTS,
    OTP_TTL_SECONDS,
    TOTP_ISSUER,
    MfaChallengePurpose,
    MfaMethodStatus,
    MfaMethodType,
    assert_can_disable_method,
    assert_challenge_usable,
    hash_mfa_secret,
    new_challenge_token,
    new_otp_code,
    new_recovery_codes,
    raise_challenge_invalid,
)
from control_plane.identity.domain.policies import PRIVILEGED_MFA_ROLES
from control_plane.identity.infrastructure.mfa_repositories import DjangoMfaRepository
from control_plane.identity.infrastructure.mfa_vault import MfaSecretVault
from control_plane.identity.models import MfaChallenge, MfaMethod
from control_plane.notifications.infrastructure.mailer import DjangoMailer
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event

_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AuthSessionResult:
    kind: str  # "session" | "mfa_challenge"
    user: UserRecord
    membership: MembershipRecord
    challenge_token: str | None = None
    methods: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class TotpEnrollResult:
    method_id: uuid.UUID
    otpauth_uri: str
    secret: str


@dataclass(frozen=True, slots=True)
class ConfirmResult:
    method_id: uuid.UUID
    method_type: str
    recovery_codes: tuple[str, ...] = ()


class MfaService:
    def __init__(
        self,
        *,
        repo: DjangoMfaRepository | None = None,
        vault: MfaSecretVault | None = None,
        mailer: DjangoMailer | None = None,
        users: UserRepository | None = None,
        memberships: MembershipRepository | None = None,
    ) -> None:
        self._repo = repo or DjangoMfaRepository()
        self._vault = vault or MfaSecretVault()
        self._mailer = mailer or DjangoMailer()
        self._users = users
        self._memberships = memberships

    def user_has_active_mfa(self, user_id: uuid.UUID) -> bool:
        return self._repo.active_count(user_id) > 0

    def list_methods(self, user_id: uuid.UUID) -> list[dict[str, object]]:
        return [self._method_public(row) for row in self._repo.list_methods(user_id)]

    def enroll_totp(self, user: UserRecord) -> TotpEnrollResult:
        secret = pyotp.random_base32()
        ciphertext = self._vault.encrypt(secret)
        method = self._repo.create_pending_totp(
            user_id=user.id, secret_ciphertext=ciphertext
        )
        uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=TOTP_ISSUER)
        log_event(_logger, "mfa.totp_enroll_started", user_id=str(user.id))
        return TotpEnrollResult(method_id=method.id, otpauth_uri=uri, secret=secret)

    def confirm_totp(self, user: UserRecord, *, method_id: uuid.UUID, code: str) -> ConfirmResult:
        method = self._require_pending(user.id, method_id, MfaMethodType.TOTP)
        secret = self._vault.decrypt(method.secret_ciphertext)
        if not pyotp.TOTP(secret).verify(code.strip(), valid_window=1):
            raise DomainError("mfa_invalid_code", "Invalid MFA code.", http_status=401)
        return self._activate(user, method)

    def enroll_email(self, user: UserRecord) -> dict[str, object]:
        method = self._repo.create_pending_email(user_id=user.id, email=user.email)
        token = new_challenge_token()
        code = new_otp_code()
        expires = self._repo.now() + timedelta(seconds=OTP_TTL_SECONDS)
        self._repo.create_challenge(
            user_id=user.id,
            purpose=MfaChallengePurpose.ENROLL,
            token=token,
            expires_at=expires,
            method_id=method.id,
            code=code,
            max_attempts=MAX_OTP_ATTEMPTS,
        )
        self._send_otp_email(user.email, code)
        log_event(_logger, "mfa.email_enroll_started", user_id=str(user.id))
        return {
            "method_id": str(method.id),
            "challenge_token": token,
            "expires_in": OTP_TTL_SECONDS,
        }

    def confirm_email(
        self, user: UserRecord, *, method_id: uuid.UUID, challenge_token: str, code: str
    ) -> ConfirmResult:
        method = self._require_pending(user.id, method_id, MfaMethodType.EMAIL)
        challenge = self._load_challenge(challenge_token)
        if challenge.user_id != user.id or challenge.purpose != MfaChallengePurpose.ENROLL.value:
            raise_challenge_invalid()
        if challenge.method_id != method.id:
            raise_challenge_invalid()
        self._verify_otp_challenge(challenge, code)
        return self._activate(user, method)

    def start_login_challenge(
        self, user: UserRecord, membership: MembershipRecord
    ) -> AuthSessionResult:
        methods = self._repo.list_active_methods(user.id)
        if not methods:
            raise DomainError("mfa_required", "MFA is required for this role.", http_status=403)
        token = new_challenge_token()
        expires = self._repo.now() + timedelta(seconds=LOGIN_CHALLENGE_TTL_SECONDS)
        self._repo.create_challenge(
            user_id=user.id,
            purpose=MfaChallengePurpose.LOGIN,
            token=token,
            expires_at=expires,
            max_attempts=MAX_OTP_ATTEMPTS,
        )
        public = tuple(
            {
                "id": str(m.id),
                "type": m.method_type,
                "email_hint": self._email_hint(m.email or user.email)
                if m.method_type == MfaMethodType.EMAIL.value
                else None,
            }
            for m in methods
        )
        log_event(_logger, "mfa.login_challenge_started", user_id=str(user.id))
        return AuthSessionResult(
            kind="mfa_challenge",
            user=user,
            membership=membership,
            challenge_token=token,
            methods=public,
        )

    def send_login_email_otp(
        self, *, challenge_token: str, method_id: uuid.UUID
    ) -> dict[str, object]:
        challenge = self._load_challenge(challenge_token)
        self._assert_login_challenge(challenge)
        method = self._repo.get_method(method_id, challenge.user_id)
        if method is None or method.status != MfaMethodStatus.ACTIVE.value:
            raise DomainError("not_found", "MFA method not found.", http_status=404)
        if method.method_type != MfaMethodType.EMAIL.value:
            raise DomainError("validation_error", "method_id must be an email MFA method.")
        user = self._repo.get_user(challenge.user_id)
        if user is None:
            raise_challenge_invalid()
        code = new_otp_code()
        challenge.method_id = method.id
        challenge.expires_at = self._repo.now() + timedelta(seconds=OTP_TTL_SECONDS)
        challenge.save(update_fields=["method_id", "expires_at"])
        self._repo.set_challenge_code(challenge, code)
        self._send_otp_email(method.email or user.email, code)
        return {"sent": True, "expires_in": OTP_TTL_SECONDS}

    def verify_login(
        self,
        *,
        challenge_token: str,
        sessions: SessionGateway,
        method_id: uuid.UUID | None = None,
        code: str | None = None,
        recovery_code: str | None = None,
    ) -> AuthSessionResult:
        if self._users is None or self._memberships is None:
            raise RuntimeError("MfaService requires user/membership repos for verify_login")
        challenge = self._load_challenge(challenge_token)
        self._assert_login_challenge(challenge)
        user = self._users.get_by_id(challenge.user_id)
        membership = self._memberships.get_for_user(challenge.user_id)
        if user is None or membership is None:
            raise_challenge_invalid()

        if recovery_code:
            ok = self._repo.consume_recovery_code(
                challenge.user_id, recovery_code.strip().lower(), now=self._repo.now()
            )
            if not ok:
                self._repo.bump_attempt(challenge)
                raise DomainError("mfa_invalid_code", "Invalid MFA code.", http_status=401)
        else:
            if method_id is None or not code:
                raise DomainError("validation_error", "method_id and code are required.")
            method = self._repo.get_method(method_id, challenge.user_id)
            if method is None or method.status != MfaMethodStatus.ACTIVE.value:
                raise DomainError("not_found", "MFA method not found.", http_status=404)
            self._verify_method_code(challenge, method, code)

        self._repo.consume_challenge(challenge, now=self._repo.now())
        sessions.create(user.id)
        log_event(_logger, "mfa.login_verified", user_id=str(user.id))
        return AuthSessionResult(kind="session", user=user, membership=membership)

    def disable_method(
        self,
        user: UserRecord,
        membership: MembershipRecord,
        *,
        method_id: uuid.UUID,
        privileged_required: bool,
        code: str | None = None,
        recovery_code: str | None = None,
        method_for_code: uuid.UUID | None = None,
    ) -> dict[str, object]:
        target = self._repo.get_method(method_id, user.id)
        if target is None or target.status != MfaMethodStatus.ACTIVE.value:
            raise DomainError("not_found", "MFA method not found.", http_status=404)
        assert_can_disable_method(
            role=membership.role,
            privileged_required=privileged_required,
            active_count=self._repo.active_count(user.id),
        )
        self._assert_step_up(
            user, code=code, recovery_code=recovery_code, method_id=method_for_code
        )
        self._repo.disable_method(target, now=self._repo.now())
        record_audit().execute(
            RecordAuditCommand(
                action="mfa.method_disabled",
                entity_type="mfa_method",
                entity_id=str(target.id),
                actor_id=user.id,
                actor_role=membership.role,
                tenant_id=membership.tenant_id,
                customer_id=membership.customer_id,
                after_summary=target.method_type,
            )
        )
        return {"disabled": True, "method_id": str(target.id)}

    def regenerate_recovery_codes(
        self,
        user: UserRecord,
        membership: MembershipRecord,
        *,
        code: str | None = None,
        recovery_code: str | None = None,
        method_id: uuid.UUID | None = None,
    ) -> tuple[str, ...]:
        if self._repo.active_count(user.id) < 1:
            raise DomainError(
                "mfa_required",
                "Enroll an MFA method before generating recovery codes.",
            )
        self._assert_step_up(user, code=code, recovery_code=recovery_code, method_id=method_id)
        codes = tuple(new_recovery_codes())
        self._repo.replace_recovery_codes(user.id, list(codes))
        record_audit().execute(
            RecordAuditCommand(
                action="mfa.recovery_regenerated",
                entity_type="user",
                entity_id=str(user.id),
                actor_id=user.id,
                actor_role=membership.role,
                tenant_id=membership.tenant_id,
                customer_id=membership.customer_id,
            )
        )
        return codes

    def admin_reset(
        self,
        *,
        actor: UserRecord,
        actor_membership: MembershipRecord,
        target_user_id: uuid.UUID,
        reason: str,
    ) -> dict[str, object]:
        cleaned = reason.strip()
        if not cleaned:
            raise DomainError("validation_error", "reason is required.")
        now = self._repo.now()
        disabled = self._repo.disable_all_for_user(target_user_id, now=now)
        self._repo.clear_recovery_codes(target_user_id)
        record_audit().execute(
            RecordAuditCommand(
                action="mfa.reset",
                entity_type="user",
                entity_id=str(target_user_id),
                actor_id=actor.id,
                actor_role=actor_membership.role,
                tenant_id=actor_membership.tenant_id,
                customer_id=actor_membership.customer_id,
                reason=cleaned[:255],
                after_summary=f"methods_disabled={disabled}",
            )
        )
        log_event(_logger, "mfa.admin_reset", target_user_id=str(target_user_id))
        return {"reset": True, "methods_disabled": disabled}

    def _activate(self, user: UserRecord, method: MfaMethod) -> ConfirmResult:
        now = self._repo.now()
        first = self._repo.active_count(user.id) == 0
        self._repo.activate_method(method, now=now)
        recovery: tuple[str, ...] = ()
        if first or not self._repo.has_recovery_codes(user.id):
            recovery = tuple(new_recovery_codes())
            self._repo.replace_recovery_codes(user.id, list(recovery))
        log_event(
            _logger,
            "mfa.method_activated",
            user_id=str(user.id),
            method_type=method.method_type,
        )
        return ConfirmResult(
            method_id=method.id,
            method_type=method.method_type,
            recovery_codes=recovery,
        )

    def _require_pending(
        self, user_id: uuid.UUID, method_id: uuid.UUID, expected: MfaMethodType
    ) -> MfaMethod:
        method = self._repo.get_method(method_id, user_id)
        if method is None:
            raise DomainError("not_found", "MFA method not found.", http_status=404)
        if method.method_type != expected.value:
            raise DomainError("validation_error", "MFA method type mismatch.")
        if method.status != MfaMethodStatus.PENDING.value:
            raise DomainError("validation_error", "MFA method is not pending confirmation.")
        return method

    def _load_challenge(self, token: str) -> MfaChallenge:
        if not token:
            raise DomainError("validation_error", "challenge_token is required.")
        challenge = self._repo.get_challenge_by_token(token)
        if challenge is None:
            raise_challenge_invalid()
        return challenge

    def _assert_login_challenge(self, challenge: MfaChallenge) -> None:
        now = self._repo.now()
        assert_challenge_usable(
            attempts=challenge.attempts,
            max_attempts=challenge.max_attempts,
            consumed=challenge.consumed_at is not None,
            expired=challenge.expires_at <= now,
        )
        if challenge.purpose != MfaChallengePurpose.LOGIN.value:
            raise_challenge_invalid()

    def _verify_otp_challenge(self, challenge: MfaChallenge, code: str) -> None:
        now = self._repo.now()
        assert_challenge_usable(
            attempts=challenge.attempts,
            max_attempts=challenge.max_attempts,
            consumed=challenge.consumed_at is not None,
            expired=challenge.expires_at <= now,
        )
        if not challenge.code_hash or hash_mfa_secret(code.strip()) != challenge.code_hash:
            self._repo.bump_attempt(challenge)
            raise DomainError("mfa_invalid_code", "Invalid MFA code.", http_status=401)
        self._repo.consume_challenge(challenge, now=now)

    def _verify_method_code(self, challenge: MfaChallenge, method: MfaMethod, code: str) -> None:
        now = self._repo.now()
        assert_challenge_usable(
            attempts=challenge.attempts,
            max_attempts=challenge.max_attempts,
            consumed=challenge.consumed_at is not None,
            expired=challenge.expires_at <= now,
        )
        cleaned = code.strip()
        if method.method_type == MfaMethodType.TOTP.value:
            secret = self._vault.decrypt(method.secret_ciphertext)
            ok = pyotp.TOTP(secret).verify(cleaned, valid_window=1)
        elif method.method_type == MfaMethodType.EMAIL.value:
            ok = bool(challenge.code_hash) and hash_mfa_secret(cleaned) == challenge.code_hash
            if challenge.method_id and challenge.method_id != method.id:
                ok = False
        else:
            ok = False
        if not ok:
            self._repo.bump_attempt(challenge)
            raise DomainError("mfa_invalid_code", "Invalid MFA code.", http_status=401)

    def _assert_step_up(
        self,
        user: UserRecord,
        *,
        code: str | None,
        recovery_code: str | None,
        method_id: uuid.UUID | None,
    ) -> None:
        if recovery_code:
            ok = self._repo.consume_recovery_code(
                user.id, recovery_code.strip().lower(), now=self._repo.now()
            )
            if not ok:
                raise DomainError("mfa_invalid_code", "Invalid MFA code.", http_status=401)
            return
        if not code or method_id is None:
            raise DomainError("validation_error", "MFA verification is required.")
        method = self._repo.get_method(method_id, user.id)
        if method is None or method.status != MfaMethodStatus.ACTIVE.value:
            raise DomainError("not_found", "MFA method not found.", http_status=404)
        cleaned = code.strip()
        if method.method_type == MfaMethodType.TOTP.value:
            secret = self._vault.decrypt(method.secret_ciphertext)
            if not pyotp.TOTP(secret).verify(cleaned, valid_window=1):
                raise DomainError("mfa_invalid_code", "Invalid MFA code.", http_status=401)
            return
        if method.method_type == MfaMethodType.EMAIL.value:
            # Email-only accounts step-up with recovery codes (or enroll TOTP).
            raise DomainError(
                "validation_error",
                "Use a TOTP method or recovery code to authorize this action.",
            )
        raise DomainError("mfa_invalid_code", "Invalid MFA code.", http_status=401)

    def _send_otp_email(self, to: str, code: str) -> None:
        # Direct mailer: do not persist OTP in notification delivery rows.
        self._mailer.send(
            to=to,
            subject="Your Vokit verification code",
            body=(
                f"Your verification code is {code}. "
                f"It expires in {OTP_TTL_SECONDS // 60} minutes."
            ),
        )

    @staticmethod
    def _method_public(row: MfaMethod) -> dict[str, object]:
        return {
            "id": str(row.id),
            "type": row.method_type,
            "status": row.status,
            "email_hint": MfaService._email_hint(row.email) if row.email else None,
            "verified_at": row.verified_at.isoformat() if row.verified_at else None,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _email_hint(email: str) -> str:
        local, _, domain = email.partition("@")
        if not domain:
            return "***"
        visible = local[:1] if local else "*"
        return f"{visible}***@{domain}"


def role_requires_mfa_when_flagged(role: str) -> bool:
    return role in PRIVILEGED_MFA_ROLES
