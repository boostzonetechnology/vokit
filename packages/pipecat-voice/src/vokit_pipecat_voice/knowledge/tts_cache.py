"""Process-local TTS audio cache for skip-LLM speak_text only.

Phone path: KnowledgeRetrieveProcessor emits TTSSpeakFrame(append_to_context=True).
Greeting uses append_to_context=False and is not cached. LLM streaming uses
TTSTextFrame and is not cached.
"""
from __future__ import annotations

import hashlib
import logging
from collections import OrderedDict
from dataclasses import dataclass

from pipecat.frames.frames import (
    Frame,
    OutputAudioRawFrame,
    TTSAudioRawFrame,
    TTSSpeakFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

logger = logging.getLogger(__name__)

_MAX_CLIPS = 64


@dataclass(frozen=True)
class CachedClip:
    audio: bytes
    sample_rate: int
    num_channels: int


_CLIPS: OrderedDict[str, CachedClip] = OrderedDict()


def cache_key(voice_id: str, text: str) -> str:
    body = f"{(voice_id or '').strip()}\n{(text or '').strip()}"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def get_clip(key: str) -> CachedClip | None:
    clip = _CLIPS.get(key)
    if clip is None:
        return None
    _CLIPS.move_to_end(key)
    return clip


def put_clip(key: str, clip: CachedClip) -> None:
    if not key or not clip.audio:
        return
    _CLIPS[key] = clip
    _CLIPS.move_to_end(key)
    while len(_CLIPS) > _MAX_CLIPS:
        _CLIPS.popitem(last=False)


def clear_clips() -> None:
    _CLIPS.clear()


class SkipPathTtsCacheGate(FrameProcessor):
    """Before TTS: replay cached skip-LLM audio or mark the speak text for capture."""

    def __init__(self, *, voice_id: str, sample_rate: int) -> None:
        super().__init__()
        self._voice_id = voice_id or ""
        self._sample_rate = sample_rate
        self.pending_key: str | None = None
        self._buffer = bytearray()
        self._capture_rate = sample_rate
        self._capture_channels = 1

    def begin_capture(self, key: str) -> None:
        self.pending_key = key
        self._buffer = bytearray()

    def append_audio(self, audio: bytes, sample_rate: int, num_channels: int) -> None:
        if not self.pending_key or not audio:
            return
        self._buffer.extend(audio)
        self._capture_rate = sample_rate
        self._capture_channels = num_channels

    def finish_capture(self) -> None:
        if not self.pending_key:
            return
        put_clip(
            self.pending_key,
            CachedClip(
                audio=bytes(self._buffer),
                sample_rate=self._capture_rate,
                num_channels=self._capture_channels,
            ),
        )
        self.pending_key = None
        self._buffer = bytearray()

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if direction != FrameDirection.DOWNSTREAM:
            await self.push_frame(frame, direction)
            return
        if isinstance(frame, TTSSpeakFrame) and getattr(frame, "append_to_context", False):
            key = cache_key(self._voice_id, frame.text or "")
            cached = get_clip(key)
            if cached is not None:
                logger.info("skip-path TTS cache hit")
                await self.push_frame(TTSStartedFrame(), direction)
                await self.push_frame(
                    TTSAudioRawFrame(
                        audio=cached.audio,
                        sample_rate=cached.sample_rate,
                        num_channels=cached.num_channels,
                    ),
                    direction,
                )
                await self.push_frame(TTSStoppedFrame(), direction)
                return
            self.begin_capture(key)
        await self.push_frame(frame, direction)


class SkipPathTtsCacheCapture(FrameProcessor):
    """After TTS: store skip-LLM audio for the pending speak text."""

    def __init__(self, gate: SkipPathTtsCacheGate) -> None:
        super().__init__()
        self._gate = gate

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if direction == FrameDirection.DOWNSTREAM and self._gate.pending_key:
            if isinstance(frame, (TTSAudioRawFrame, OutputAudioRawFrame)):
                audio = getattr(frame, "audio", b"") or b""
                if audio:
                    self._gate.append_audio(
                        audio,
                        int(getattr(frame, "sample_rate", None) or 8000),
                        int(getattr(frame, "num_channels", None) or 1),
                    )
            if isinstance(frame, TTSStoppedFrame):
                self._gate.finish_capture()
        await self.push_frame(frame, direction)
