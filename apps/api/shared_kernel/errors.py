from __future__ import annotations


class DomainError(Exception):
    """Stable machine-readable failure. Mapped once at the HTTP boundary."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, object] | None = None,
        http_status: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.http_status = http_status


class NotFoundError(DomainError):
    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__("not_found", message, http_status=404)
