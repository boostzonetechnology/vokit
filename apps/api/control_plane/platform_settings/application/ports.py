from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class SettingRecord:
    key: str
    value: Any
    secret: bool
    updated_by_id: uuid.UUID | None


@dataclass(frozen=True, slots=True)
class AgencyFlagRecord:
    tenant_id: uuid.UUID
    flag: str
    enabled: bool
    updated_by_id: uuid.UUID | None


class SettingRepository(Protocol):
    def get(self, key: str) -> SettingRecord | None: ...
    def upsert(self, record: SettingRecord) -> SettingRecord: ...
    def list_all(self) -> list[SettingRecord]: ...


class AgencyFlagRepository(Protocol):
    def list_all(self) -> list[AgencyFlagRecord]: ...
    def upsert(self, record: AgencyFlagRecord) -> AgencyFlagRecord: ...
