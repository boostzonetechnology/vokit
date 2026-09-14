"""MFA persistence helpers."""

from __future__ import annotations

import uuid
from datetime import datetime

from django.utils import timezone

from control_plane.identity.domain.mfa import (
    MfaChallengePurpose,
    MfaMethodStatus,
    MfaMethodType,
    hash_mfa_secret,
)
from control_plane.identity.models import MfaChallenge, MfaMethod, MfaRecoveryCode, User
from shared_kernel.ids import new_uuid7


class DjangoMfaRepository:
    def list_methods(self, user_id: uuid.UUID) -> list[MfaMethod]:
        return list(MfaMethod.objects.filter(user_id=user_id).order_by("created_at"))

    def list_active_methods(self, user_id: uuid.UUID) -> list[MfaMethod]:
        return list(
            MfaMethod.objects.filter(
                user_id=user_id, status=MfaMethodStatus.ACTIVE.value
            ).order_by("created_at")
        )

    def active_count(self, user_id: uuid.UUID) -> int:
        return MfaMethod.objects.filter(
            user_id=user_id, status=MfaMethodStatus.ACTIVE.value
        ).count()

    def get_method(self, method_id: uuid.UUID, user_id: uuid.UUID) -> MfaMethod | None:
        return MfaMethod.objects.filter(id=method_id, user_id=user_id).first()

    def create_pending_totp(
        self, *, user_id: uuid.UUID, secret_ciphertext: str
    ) -> MfaMethod:
        return MfaMethod.objects.create(
            id=new_uuid7(),
            user_id=user_id,
            method_type=MfaMethodType.TOTP.value,
            status=MfaMethodStatus.PENDING.value,
            secret_ciphertext=secret_ciphertext,
        )

    def create_pending_email(self, *, user_id: uuid.UUID, email: str) -> MfaMethod:
        return MfaMethod.objects.create(
            id=new_uuid7(),
            user_id=user_id,
            method_type=MfaMethodType.EMAIL.value,
            status=MfaMethodStatus.PENDING.value,
            email=email,
        )

    def activate_method(self, method: MfaMethod, *, now: datetime) -> None:
        method.status = MfaMethodStatus.ACTIVE.value
        method.verified_at = now
        method.save(update_fields=["status", "verified_at"])

    def disable_method(self, method: MfaMethod, *, now: datetime) -> None:
        method.status = MfaMethodStatus.DISABLED.value
        method.disabled_at = now
        method.save(update_fields=["status", "disabled_at"])

    def disable_all_for_user(self, user_id: uuid.UUID, *, now: datetime) -> int:
        statuses = [MfaMethodStatus.PENDING.value, MfaMethodStatus.ACTIVE.value]
        return MfaMethod.objects.filter(user_id=user_id, status__in=statuses).update(
            status=MfaMethodStatus.DISABLED.value,
            disabled_at=now,
        )

    def create_challenge(
        self,
        *,
        user_id: uuid.UUID,
        purpose: MfaChallengePurpose,
        token: str,
        expires_at: datetime,
        method_id: uuid.UUID | None = None,
        code: str | None = None,
        max_attempts: int = 5,
    ) -> MfaChallenge:
        return MfaChallenge.objects.create(
            id=new_uuid7(),
            user_id=user_id,
            purpose=purpose.value,
            method_id=method_id,
            token_hash=hash_mfa_secret(token),
            code_hash=hash_mfa_secret(code) if code else "",
            expires_at=expires_at,
            max_attempts=max_attempts,
        )

    def get_challenge_by_token(self, token: str) -> MfaChallenge | None:
        return (
            MfaChallenge.objects.select_related("method", "user")
            .filter(token_hash=hash_mfa_secret(token))
            .first()
        )

    def set_challenge_code(self, challenge: MfaChallenge, code: str) -> None:
        challenge.code_hash = hash_mfa_secret(code)
        challenge.attempts = 0
        challenge.save(update_fields=["code_hash", "attempts"])

    def bump_attempt(self, challenge: MfaChallenge) -> None:
        challenge.attempts += 1
        challenge.save(update_fields=["attempts"])

    def consume_challenge(self, challenge: MfaChallenge, *, now: datetime) -> None:
        challenge.consumed_at = now
        challenge.save(update_fields=["consumed_at"])

    def replace_recovery_codes(self, user_id: uuid.UUID, codes: list[str]) -> None:
        MfaRecoveryCode.objects.filter(user_id=user_id).delete()
        MfaRecoveryCode.objects.bulk_create(
            [
                MfaRecoveryCode(
                    id=new_uuid7(),
                    user_id=user_id,
                    code_hash=hash_mfa_secret(code),
                )
                for code in codes
            ]
        )

    def consume_recovery_code(self, user_id: uuid.UUID, code: str, *, now: datetime) -> bool:
        row = MfaRecoveryCode.objects.filter(
            user_id=user_id,
            code_hash=hash_mfa_secret(code),
            used_at__isnull=True,
        ).first()
        if row is None:
            return False
        row.used_at = now
        row.save(update_fields=["used_at"])
        return True

    def clear_recovery_codes(self, user_id: uuid.UUID) -> None:
        MfaRecoveryCode.objects.filter(user_id=user_id).delete()

    def has_recovery_codes(self, user_id: uuid.UUID) -> bool:
        return MfaRecoveryCode.objects.filter(user_id=user_id).exists()

    def get_user(self, user_id: uuid.UUID) -> User | None:
        return User.objects.filter(pk=user_id).first()

    def now(self) -> datetime:
        return timezone.now()
