from __future__ import annotations

import uuid
from typing import Protocol

from django.conf import settings
from django.core import signing

from control_plane.tenancy.models import TenantDbCredential
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7

_VAULT_SALT = "tenant_db_pwd"


class TenantDbVault(Protocol):
    def put(self, database_id: uuid.UUID, plaintext: str) -> None: ...

    def get(self, database_id: uuid.UUID) -> str: ...


class DjangoTenantDbVault:
    """Encrypts tenant DB passwords at rest. Never expose via Agency APIs."""

    def put(self, database_id: uuid.UUID, plaintext: str) -> None:
        if not plaintext:
            raise DomainError(
                "secret_missing",
                "Required secret is not configured.",
                http_status=503,
            )
        ciphertext = signing.dumps(
            plaintext,
            salt=_VAULT_SALT,
            key=settings.SECRET_KEY,
        )
        row = TenantDbCredential.objects.filter(database_id=database_id).first()
        if row is None:
            TenantDbCredential.objects.create(
                id=new_uuid7(),
                database_id=database_id,
                ciphertext=ciphertext[:1024],
            )
            return
        row.ciphertext = ciphertext[:1024]
        row.save(update_fields=["ciphertext", "updated_at"])

    def get(self, database_id: uuid.UUID) -> str:
        row = TenantDbCredential.objects.filter(database_id=database_id).first()
        if row is None or not row.ciphertext:
            raise DomainError(
                "secret_missing",
                "Required secret is not configured.",
                http_status=503,
            )
        try:
            value = signing.loads(
                row.ciphertext,
                salt=_VAULT_SALT,
                key=settings.SECRET_KEY,
            )
        except signing.BadSignature as exc:
            raise DomainError(
                "secret_missing",
                "Required secret is not configured.",
                http_status=503,
            ) from exc
        if not isinstance(value, str) or not value:
            raise DomainError(
                "secret_missing",
                "Required secret is not configured.",
                http_status=503,
            )
        return value
