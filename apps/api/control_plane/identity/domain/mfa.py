"""MFA domain types and policies (SEC-013 / RBAC-008)."""

from __future__ import annotations

import hashlib
import secrets
from enum import StrEnum

from control_plane.identity.domain.policies import PRIVILEGED_MFA_ROLES
from shared_kernel.errors import DomainError

OTP_TTL_SECONDS = 600
LOGIN_CHALLENGE_TTL_SECONDS = 600
MAX_OTP_ATTEMPTS = 5
RECOVERY_CODE_COUNT = 10
TOTP_ISSUER = "Vokit"


class MfaMethodType(StrEnum):
    TOTP = "totp"
    EMAIL = "email"


class MfaMethodStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"


class MfaChallengePurpose(StrEnum):
    LOGIN = "login"
    ENROLL = "enroll"
    DISABLE = "disable"


def hash_mfa_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_challenge_token() -> str:
    return secrets.token_urlsafe(32)


def new_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def new_recovery_codes(count: int = RECOVERY_CODE_COUNT) -> list[str]:
    return [secrets.token_hex(4) for _ in range(count)]


def assert_can_disable_method(
    *,
    role: str,
    privileged_required: bool,
    active_count: int,
) -> None:
    if active_count <= 1 and privileged_required and role in PRIVILEGED_MFA_ROLES:
        raise DomainError(
            "mfa_last_method",
            "Cannot disable the last MFA method while MFA is required for this role.",
            http_status=409,
        )


def assert_challenge_usable(
    *, attempts: int, max_attempts: int, consumed: bool, expired: bool
) -> None:
    if consumed:
        raise DomainError(
            "mfa_challenge_invalid",
            "MFA challenge is no longer valid.",
            http_status=401,
        )
    if expired:
        raise DomainError("mfa_challenge_expired", "MFA challenge expired.", http_status=401)
    if attempts >= max_attempts:
        raise DomainError("mfa_challenge_locked", "Too many MFA attempts.", http_status=429)


def raise_challenge_invalid() -> None:
    raise DomainError(
        "mfa_challenge_invalid",
        "MFA challenge is no longer valid.",
        http_status=401,
    )
