from __future__ import annotations

from shared_kernel.ids import is_uuid, new_uuid7


def test_uuid7_version_and_uniqueness() -> None:
    first = new_uuid7()
    second = new_uuid7()
    assert first.version == 7
    assert second.version == 7
    assert first != second
    assert is_uuid(str(first))
    assert not is_uuid("not-a-uuid")
