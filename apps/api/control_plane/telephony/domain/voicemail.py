from __future__ import annotations

from enum import StrEnum

from shared_kernel.errors import DomainError


class VoicemailDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class VoicemailStatus(StrEnum):
    RECORDING = "recording"
    READY = "ready"
    FAILED = "failed"


class VoicemailAction(StrEnum):
    START = "start"
    COMPLETE = "complete"
    FAIL = "fail"


def assert_voicemail_direction(raw: str) -> VoicemailDirection:
    try:
        return VoicemailDirection((raw or "").strip().lower())
    except ValueError as exc:
        raise DomainError("validation_error", "voicemail direction is invalid.") from exc


def assert_voicemail_action(raw: str) -> VoicemailAction:
    try:
        return VoicemailAction((raw or "").strip().lower())
    except ValueError as exc:
        raise DomainError("validation_error", "voicemail action is invalid.") from exc


def next_voicemail_status(action: VoicemailAction) -> VoicemailStatus:
    if action is VoicemailAction.START:
        return VoicemailStatus.RECORDING
    if action is VoicemailAction.COMPLETE:
        return VoicemailStatus.READY
    return VoicemailStatus.FAILED
