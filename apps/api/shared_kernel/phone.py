"""E.164 storage (NFR-012). Display formatting stays at the API/UI boundary."""

from __future__ import annotations

import re

from shared_kernel.errors import DomainError

_E164 = re.compile(r"^\+[1-9]\d{7,14}$")


def normalize_e164(raw: str) -> str:
    compact = re.sub(r"[\s().-]", "", (raw or "").strip())
    if compact.startswith("00"):
        compact = "+" + compact[2:]
    if not compact.startswith("+"):
        raise DomainError("invalid_phone", "Phone numbers must be provided in E.164.")
    if not _E164.fullmatch(compact):
        raise DomainError("invalid_phone", "Phone numbers must be provided in E.164.")
    return compact
