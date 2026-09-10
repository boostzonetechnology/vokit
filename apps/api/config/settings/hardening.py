from __future__ import annotations

from shared_kernel.errors import DomainError


def assert_production_boot(
    *,
    allowed_hosts: list[str],
    telephony_token: str,
    recording_token: str,
    cors_origins: list[str],
    csrf_origins: list[str],
    tenant_runtime: str,
    tenant_tls_required: bool,
) -> None:
    if not allowed_hosts or allowed_hosts == ["localhost", "127.0.0.1"]:
        raise DomainError(
            "invalid_configuration",
            "DJANGO_ALLOWED_HOSTS must be set in production.",
        )
    if not telephony_token.strip():
        raise DomainError(
            "invalid_configuration",
            "VOKIT_INTERNAL_TELEPHONY_TOKEN is required in production.",
        )
    if not recording_token.strip():
        raise DomainError(
            "invalid_configuration",
            "VOKIT_INTERNAL_RECORDING_TOKEN is required in production.",
        )
    if telephony_token.strip() == recording_token.strip():
        raise DomainError(
            "invalid_configuration",
            "Recording token must differ from the telephony token.",
        )
    if not cors_origins:
        raise DomainError(
            "invalid_configuration",
            "CORS_ALLOWED_ORIGINS must be set in production.",
        )
    if not csrf_origins:
        raise DomainError(
            "invalid_configuration",
            "CSRF_TRUSTED_ORIGINS must be set in production.",
        )
    if tenant_runtime != "mysql":
        raise DomainError(
            "invalid_configuration",
            "TENANT_RUNTIME must be mysql in production.",
        )
    if not tenant_tls_required:
        raise DomainError(
            "invalid_configuration",
            "TENANT_TLS_REQUIRED must be true in production.",
        )
