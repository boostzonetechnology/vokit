from __future__ import annotations

from dataclasses import dataclass

from control_plane.identity.application.mfa import AuthSessionResult, MfaService
from control_plane.identity.application.ports import (
    LoginRateLimiter,
    MembershipRepository,
    PasswordHasher,
    SessionGateway,
    UserRepository,
)
from control_plane.identity.domain.policies import (
    assert_privileged_mfa,
    assert_user_can_authenticate,
    normalize_email,
)
from control_plane.identity.domain.types import MembershipStatus
from shared_kernel.errors import DomainError


@dataclass(frozen=True, slots=True)
class AuthenticateCommand:
    email: str
    password: str
    rate_key: str
    privileged_mfa_required: bool = False


class AuthenticateUser:
    def __init__(
        self,
        users: UserRepository,
        memberships: MembershipRepository,
        passwords: PasswordHasher,
        sessions: SessionGateway,
        limiter: LoginRateLimiter,
        mfa: MfaService | None = None,
    ) -> None:
        self._users = users
        self._memberships = memberships
        self._passwords = passwords
        self._sessions = sessions
        self._limiter = limiter
        self._mfa = mfa or MfaService(users=users, memberships=memberships)

    def execute(self, command: AuthenticateCommand) -> AuthSessionResult:
        if not self._limiter.allow(command.rate_key):
            raise DomainError(
                "rate_limited",
                "Too many attempts. Try again later.",
                http_status=429,
            )
        try:
            email = normalize_email(command.email)
        except DomainError as exc:
            self._limiter.register_failure(command.rate_key)
            raise DomainError(
                "unauthenticated",
                "Invalid email or password.",
                http_status=401,
            ) from exc
        user = self._users.get_by_email(email)
        if user is None or not self._passwords.verify(command.password, user.password_hash):
            self._limiter.register_failure(command.rate_key)
            raise DomainError("unauthenticated", "Invalid email or password.", http_status=401)
        try:
            assert_user_can_authenticate(user.status)
        except DomainError as exc:
            self._limiter.register_failure(command.rate_key)
            raise DomainError(
                "unauthenticated",
                "Invalid email or password.",
                http_status=401,
            ) from exc
        membership = self._memberships.get_for_user(user.id)
        if membership is None or membership.status is not MembershipStatus.ACTIVE:
            self._limiter.register_failure(command.rate_key)
            raise DomainError("unauthenticated", "Invalid email or password.", http_status=401)

        enrolled = self._mfa.user_has_active_mfa(user.id)
        assert_privileged_mfa(
            role=membership.role,
            required=command.privileged_mfa_required,
            enrolled=enrolled,
        )

        if enrolled:
            self._limiter.reset(command.rate_key)
            return self._mfa.start_login_challenge(user, membership)

        self._sessions.create(user.id)
        self._limiter.reset(command.rate_key)
        return AuthSessionResult(kind="session", user=user, membership=membership)
