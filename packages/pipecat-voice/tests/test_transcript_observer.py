"""User transcript observer must not block the STT → LLM critical path."""
from __future__ import annotations

import asyncio

import pytest
from pipecat.frames.frames import EndFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection

from vokit_pipecat_voice.django_client import DjangoUnreachable
from vokit_pipecat_voice.pipeline.session import _UserTranscriptObserver


class _SlowDjango:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.calls = 0

    async def send_event(self, **kwargs):
        self.calls += 1
        self.started.set()
        await self.release.wait()
        return {"ok": True, "continue_call": True}


class _FailDjango:
    async def send_event(self, **kwargs):
        raise DjangoUnreachable("down")


class _StopDjango:
    async def send_event(self, **kwargs):
        return {"ok": True, "continue_call": False, "reason": "stop"}


@pytest.mark.asyncio
async def test_transcript_pushed_before_django_returns():
    django = _SlowDjango()
    observer = _UserTranscriptObserver(django, "call-1")  # type: ignore[arg-type]
    pushed: list = []

    async def capture(frame, direction=FrameDirection.DOWNSTREAM):
        pushed.append(frame)

    observer.push_frame = capture  # type: ignore[method-assign]

    frame = TranscriptionFrame(text="hello there", user_id="", timestamp="")
    await observer.process_frame(frame, FrameDirection.DOWNSTREAM)

    # Critical path: TranscriptionFrame already downstream while Django is still pending.
    assert any(isinstance(f, TranscriptionFrame) for f in pushed)
    await asyncio.wait_for(django.started.wait(), timeout=1.0)
    assert django.calls == 1
    assert not django.release.is_set()

    django.release.set()
    await asyncio.sleep(0.05)
    assert not any(isinstance(f, EndFrame) for f in pushed)


@pytest.mark.asyncio
async def test_django_unreachable_still_fail_closes():
    observer = _UserTranscriptObserver(_FailDjango(), "call-2")  # type: ignore[arg-type]
    pushed: list = []

    async def capture(frame, direction=FrameDirection.DOWNSTREAM):
        pushed.append(frame)

    observer.push_frame = capture  # type: ignore[method-assign]

    await observer.process_frame(
        TranscriptionFrame(text="hi", user_id="", timestamp=""),
        FrameDirection.DOWNSTREAM,
    )
    await asyncio.sleep(0.05)
    assert any(isinstance(f, TranscriptionFrame) for f in pushed)
    assert any(isinstance(f, EndFrame) for f in pushed)


@pytest.mark.asyncio
async def test_continue_call_false_emits_end_frame():
    observer = _UserTranscriptObserver(_StopDjango(), "call-3")  # type: ignore[arg-type]
    pushed: list = []

    async def capture(frame, direction=FrameDirection.DOWNSTREAM):
        pushed.append(frame)

    observer.push_frame = capture  # type: ignore[method-assign]

    await observer.process_frame(
        TranscriptionFrame(text="bye", user_id="", timestamp=""),
        FrameDirection.DOWNSTREAM,
    )
    await asyncio.sleep(0.05)
    assert any(isinstance(f, EndFrame) for f in pushed)
