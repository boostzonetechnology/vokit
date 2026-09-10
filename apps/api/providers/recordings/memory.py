from __future__ import annotations

from dataclasses import dataclass

from shared_kernel.errors import DomainError


class RecordingStoreUnavailable(DomainError):
    def __init__(self) -> None:
        super().__init__(
            "recording_store_unavailable",
            "Recording store is unavailable.",
            http_status=503,
        )


@dataclass(frozen=True, slots=True)
class StoredObject:
    object_key: str
    checksum: str
    size_bytes: int


class MemoryRecordingStore:
    """In-process recording plane. Registers object existence only — no Django files."""

    def __init__(self) -> None:
        self._objects: dict[str, StoredObject] = {}
        self.down = False

    def reset(self) -> None:
        self._objects.clear()
        self.down = False

    def mark_down(self, down: bool = True) -> None:
        self.down = down

    def put(self, *, object_key: str, checksum: str, size_bytes: int) -> StoredObject:
        self._guard()
        stored = StoredObject(
            object_key=object_key, checksum=checksum, size_bytes=size_bytes
        )
        existing = self._objects.get(object_key)
        if existing is not None and existing.checksum != checksum:
            raise DomainError(
                "conflict_state",
                "Recording objects are immutable.",
                http_status=409,
            )
        self._objects[object_key] = stored
        return stored

    def exists(self, object_key: str) -> bool:
        self._guard()
        return object_key in self._objects

    def get(self, object_key: str) -> StoredObject | None:
        self._guard()
        return self._objects.get(object_key)

    def list_keys(self) -> list[str]:
        self._guard()
        return list(self._objects)

    def _guard(self) -> None:
        if self.down:
            raise RecordingStoreUnavailable()
