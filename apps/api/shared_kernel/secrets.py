"""Secret references only. Models store the key name, never the plaintext."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from shared_kernel.errors import DomainError


@dataclass(frozen=True, slots=True)
class SecretRef:
    key: str
    provider: str = "env"

    def __post_init__(self) -> None:
        if not self.key or self.key != self.key.strip() or any(ch.isspace() for ch in self.key):
            raise DomainError("invalid_secret_ref", "Secret reference key is invalid.")
        if self.provider != "env":
            raise DomainError("unsupported_secret_provider", "Phase 1 secret provider is env only.")

    def resolve(self, environ: Mapping[str, str] | None = None) -> str:
        value = self.resolve_optional(environ)
        if value == "":
            raise DomainError(
                "secret_missing",
                "Required secret is not configured.",
                http_status=503,
            )
        return value

    def resolve_optional(self, environ: Mapping[str, str] | None = None) -> str:
        env = environ if environ is not None else os.environ
        return (env.get(self.key, "") or "").strip()

    def __str__(self) -> str:
        return f"SecretRef({self.provider}:{self.key})"

    def __repr__(self) -> str:
        return f"SecretRef(provider={self.provider!r}, key={self.key!r})"
