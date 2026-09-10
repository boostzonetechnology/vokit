from __future__ import annotations

from enum import StrEnum


class ArtifactKind(StrEnum):
    CALL_RECORDING = "call_recording"
    VOICEMAIL = "voicemail"
    TRANSCRIPT = "transcript"


class ArtifactStatus(StrEnum):
    ANNOUNCED = "announced"
    VERIFYING = "verifying"
    READY = "ready"
    FAILED = "failed"
    RETAINED = "retained"
    DELETED = "deleted"


class GrantStatus(StrEnum):
    ISSUED = "issued"
    CONSUMED = "consumed"
    EXPIRED = "expired"
