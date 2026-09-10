"""UUID v7 (RFC 9562). Time-sortable, non-enumerable enough for public IDs."""

from __future__ import annotations

import os
import time
import uuid


def new_uuid7() -> uuid.UUID:
    timestamp_ms = int(time.time() * 1000)
    if timestamp_ms < 0 or timestamp_ms >= 1 << 48:
        raise ValueError("timestamp out of UUID v7 range")
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
    rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)
    value = (timestamp_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
    return uuid.UUID(int=value)


def uuid7_str() -> str:
    return str(new_uuid7())


def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except (ValueError, TypeError, AttributeError):
        return False
    return True
