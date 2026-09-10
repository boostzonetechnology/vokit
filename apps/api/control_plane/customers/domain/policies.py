from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from shared_kernel.errors import DomainError
from shared_kernel.phone import normalize_e164


@dataclass(frozen=True, slots=True)
class BanKey:
    kind: str
    value: str


ALLOWED_BAN_KINDS = frozenset({"email", "phone", "external_ref"})


def normalize_ban_key(key: BanKey) -> BanKey:
    kind = (key.kind or "").strip().lower()
    value = (key.value or "").strip()
    if kind not in ALLOWED_BAN_KINDS:
        raise DomainError("validation_error", "Ban key kind is invalid.")
    if not value:
        raise DomainError("validation_error", "Ban key value is required.")
    if kind == "email":
        value = value.lower()
        if "@" not in value:
            raise DomainError("validation_error", "Ban email is invalid.")
    elif kind == "phone":
        value = normalize_e164(value)
    else:
        value = value[:128]
    return BanKey(kind=kind, value=value)


def hash_ban_key(key: BanKey) -> str:
    normalized = normalize_ban_key(key)
    material = f"{normalized.kind}:{normalized.value}".encode()
    return hashlib.sha256(material).hexdigest()


def ineligible_customer() -> DomainError:
    return DomainError(
        "customer_ineligible",
        "Customer is not eligible.",
        http_status=409,
    )


def customer_not_found() -> DomainError:
    return DomainError("not_found", "Resource not found.", http_status=404)


def reassignment_forbidden() -> DomainError:
    return DomainError(
        "customer_reassign_forbidden",
        "Customer reassignment is not available.",
        http_status=409,
    )


def assert_customer_stays_on_tenant(
    *,
    indexed_tenant_id: uuid.UUID,
    route_tenant_id: uuid.UUID,
) -> None:
    if indexed_tenant_id != route_tenant_id:
        raise reassignment_forbidden()
