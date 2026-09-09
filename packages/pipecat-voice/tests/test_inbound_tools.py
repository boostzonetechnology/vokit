"""Inbound transfer tool delegates to Django (no local pre-check)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from vokit_pipecat_voice.pipeline.inbound_tools import build_inbound_tools


@pytest.mark.asyncio
async def test_transfer_tool_pending_then_completed():
    django = AsyncMock()
    django.request_transfer = AsyncMock(
        return_value={
            "ok": True,
            "available": True,
            "continue_call": True,
            "status": "pending",
        },
    )
    django.poll_transfer_until_terminal = AsyncMock(
        return_value={
            "ok": True,
            "available": True,
            "continue_call": False,
            "reason": "transferred",
            "status": "succeeded",
        },
    )
    on_success = AsyncMock()
    tools = build_inbound_tools(
        django=django,
        edge_call_id="edge-1",
        transfer_spec={"configured": True},
        on_transfer_success=on_success,
    )
    params = MagicMock()
    params.result_callback = AsyncMock()
    await tools[0].handler(params)
    django.request_transfer.assert_awaited_once_with(edge_call_id="edge-1")
    django.poll_transfer_until_terminal.assert_awaited_once_with(edge_call_id="edge-1")
    params.result_callback.assert_awaited_once_with(
        {
            "ok": True,
            "available": True,
            "continue_call": False,
            "reason": "transferred",
            "status": "succeeded",
        },
    )
    on_success.assert_awaited_once()


@pytest.mark.asyncio
async def test_transfer_tool_pending_then_failed_no_endframe():
    django = AsyncMock()
    django.request_transfer = AsyncMock(
        return_value={
            "ok": True,
            "available": True,
            "continue_call": True,
            "status": "pending",
        },
    )
    django.poll_transfer_until_terminal = AsyncMock(
        return_value={
            "ok": False,
            "available": True,
            "continue_call": True,
            "reason": "no_answer",
            "status": "idle",
        },
    )
    on_success = AsyncMock()
    tools = build_inbound_tools(
        django=django,
        edge_call_id="edge-1",
        transfer_spec={"configured": True},
        on_transfer_success=on_success,
    )
    params = MagicMock()
    params.result_callback = AsyncMock()
    await tools[0].handler(params)
    on_success.assert_not_awaited()


@pytest.mark.asyncio
async def test_transfer_tool_immediate_failure():
    django = AsyncMock()
    django.request_transfer = AsyncMock(
        return_value={
            "ok": False,
            "available": False,
            "continue_call": True,
            "reason": "unavailable",
        },
    )
    on_success = AsyncMock()
    tools = build_inbound_tools(
        django=django,
        edge_call_id="edge-1",
        transfer_spec={"configured": True},
        on_transfer_success=on_success,
    )
    params = MagicMock()
    params.result_callback = AsyncMock()
    await tools[0].handler(params)
    django.poll_transfer_until_terminal.assert_not_called()
    on_success.assert_not_awaited()


@pytest.mark.asyncio
async def test_transfer_tool_not_registered_when_unconfigured():
    django = AsyncMock()
    tools = build_inbound_tools(
        django=django,
        edge_call_id="edge-1",
        transfer_spec={"configured": False},
        on_transfer_success=AsyncMock(),
    )
    assert tools == []
