from __future__ import annotations


class MemorySecretVault:
    """In-process secret store. Values never appear in API payloads or logs."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def reset(self) -> None:
        self._values.clear()

    def put(self, secret_ref: str, value: str) -> None:
        self._values[secret_ref] = value

    def get(self, secret_ref: str) -> str:
        return self._values.get(secret_ref, "")

    def delete(self, secret_ref: str) -> None:
        self._values.pop(secret_ref, None)
