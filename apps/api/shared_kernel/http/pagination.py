from __future__ import annotations

from shared_kernel.errors import DomainError


def parse_page(
    raw_limit: object,
    raw_offset: object,
    *,
    default_limit: int = 50,
    hard_max: int = 50,
) -> tuple[int, int]:
    try:
        limit = int(raw_limit) if raw_limit not in (None, "") else default_limit
        offset = int(raw_offset) if raw_offset not in (None, "") else 0
    except (TypeError, ValueError) as exc:
        raise DomainError("validation_error", "Pagination is invalid.") from exc
    if limit < 1 or offset < 0:
        raise DomainError("validation_error", "Pagination is invalid.")
    return min(limit, hard_max), offset


def page_slice(items: list, offset: int, limit: int) -> tuple[list, dict]:
    sliced = items[offset : offset + limit]
    nxt = offset + limit if offset + limit < len(items) else None
    return sliced, {"next": nxt, "limit": limit, "offset": offset}
