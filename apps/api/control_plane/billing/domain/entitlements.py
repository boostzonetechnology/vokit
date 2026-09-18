from __future__ import annotations

from shared_kernel.errors import DomainError

PENDING_UPGRADE = "upgrade"
PENDING_DOWNGRADE = "downgrade"


def _cap_tighter(new: int, old: int) -> bool:
    if new < 1:
        return False
    return old < 1 or new < old


def entitlements_tighter(
    *,
    new_max_agents: int,
    old_max_agents: int,
    new_max_phone_numbers: int,
    old_max_phone_numbers: int,
    new_max_concurrency: int,
    old_max_concurrency: int,
    new_recording_allowed: bool,
    old_recording_allowed: bool,
    new_integrations: tuple[str, ...],
    old_integrations: tuple[str, ...],
) -> bool:
    if _cap_tighter(new_max_agents, old_max_agents):
        return True
    if _cap_tighter(new_max_phone_numbers, old_max_phone_numbers):
        return True
    if _cap_tighter(new_max_concurrency, old_max_concurrency):
        return True
    if old_recording_allowed and not new_recording_allowed:
        return True
    new_set = set(new_integrations)
    old_set = set(old_integrations)
    if new_set and not old_set:
        return True
    if new_set and old_set and not new_set.issuperset(old_set):
        return True
    return False


def assert_agent_cap(*, max_agents: int, active_count: int) -> None:
    if max_agents < 1:
        return
    if active_count >= max_agents:
        raise DomainError(
            "plan_limit_agents",
            "This plan does not allow more active agents.",
            http_status=409,
        )


def assert_number_cap(*, max_phone_numbers: int, assigned_count: int) -> None:
    if max_phone_numbers < 1:
        return
    if assigned_count >= max_phone_numbers:
        raise DomainError(
            "plan_limit_numbers",
            "This plan does not allow more phone numbers.",
            http_status=409,
        )


def assert_concurrency_cap(*, max_concurrency: int, live_count: int) -> str | None:
    if max_concurrency < 1:
        return None
    if live_count >= max_concurrency:
        return "concurrency_limit"
    return None


def assert_recording_allowed(*, allowed: bool) -> None:
    if not allowed:
        raise DomainError(
            "plan_recording_disabled",
            "This plan does not allow recordings.",
            http_status=409,
        )


def assert_integration_allowed(*, allowed: tuple[str, ...], provider: str) -> None:
    if not allowed:
        return
    if provider not in allowed:
        raise DomainError(
            "plan_integration_not_allowed",
            "This plan does not allow that integration.",
            http_status=409,
        )


def assert_extras_fit(
    *,
    max_agents: int,
    active_agents: int,
    max_phone_numbers: int,
    assigned_numbers: int,
) -> None:
    if max_agents > 0 and active_agents > max_agents:
        raise DomainError(
            "extras_exceed_plan",
            "Archive or pause extra agents before this downgrade.",
            http_status=409,
        )
    if max_phone_numbers > 0 and assigned_numbers > max_phone_numbers:
        raise DomainError(
            "extras_exceed_plan",
            "Release extra numbers before this downgrade.",
            http_status=409,
        )
