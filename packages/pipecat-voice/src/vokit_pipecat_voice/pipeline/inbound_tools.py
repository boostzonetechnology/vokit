"""LLM tools for inbound phone sessions."""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from pipecat.adapters.schemas.function_schema import FunctionSchema

from vokit_pipecat_voice.django_client import DjangoUnreachable, DjangoVoiceClient

logger = logging.getLogger(__name__)

_TRANSFER_TOOL_DESCRIPTION = (
    "Call when the caller clearly wants to speak with a human or be transferred. "
    "Do not use for general questions answerable from knowledge or instructions. "
    "Returns machine reason codes only (not caller-facing wording): "
    "transferred (human connected, stop assisting), no_answer, timeout, transfer_failed, "
    "unavailable, not_configured. Use agent instructions for what to say to the caller."
)


def build_inbound_tools(
    *,
    django: DjangoVoiceClient,
    edge_call_id: str,
    transfer_spec: dict[str, Any],
    on_transfer_success: Callable[[], Awaitable[None]],
) -> list[FunctionSchema]:
    if not transfer_spec.get("configured"):
        return []

    async def _request_call_transfer(params):
        try:
            result = await django.request_transfer(edge_call_id=edge_call_id)
        except DjangoUnreachable as exc:
            await params.result_callback(
                {
                    "ok": False,
                    "available": False,
                    "error": str(exc),
                }
            )
            return

        if result.get("status") == "pending":
            try:
                result = await django.poll_transfer_until_terminal(edge_call_id=edge_call_id)
            except DjangoUnreachable as exc:
                await params.result_callback(
                    {
                        "ok": False,
                        "available": False,
                        "error": str(exc),
                    }
                )
                return

        await params.result_callback(result)
        if result.get("ok") and result.get("continue_call") is False:
            logger.info(
                "transfer completed edge_call_id=%s — stopping AI pipeline",
                edge_call_id,
            )
            await on_transfer_success()

    return [
        FunctionSchema(
            name="request_call_transfer",
            description=_TRANSFER_TOOL_DESCRIPTION,
            properties={},
            required=[],
            handler=_request_call_transfer,
        ),
    ]
