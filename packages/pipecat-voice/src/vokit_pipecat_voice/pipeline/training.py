"""Browser Developer Training pipeline (SmallWebRTC). No SIP, no billing, never skip-LLM."""
from __future__ import annotations

import logging
from typing import Any

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.frames.frames import TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.workers.runner import WorkerRunner

from vokit_pipecat_voice.config import PipecatVoiceConfig
from vokit_pipecat_voice.django_client import DjangoUnreachable, DjangoVoiceClient
from vokit_pipecat_voice.pipeline.analyzers import build_vad_and_turn_analyzers
from vokit_pipecat_voice.pipeline.inbound_path import user_aggregator_params
from vokit_pipecat_voice.providers.mapper import UnsupportedProviderError, build_pipeline_services

logger = logging.getLogger(__name__)

# Browser WebRTC is not the phone μ-law path. Do not reuse 8 kHz from /sip/media.
TRAINING_AUDIO_IN_SAMPLE_RATE = 16000
TRAINING_AUDIO_OUT_SAMPLE_RATE = 24000


def _tool_args(params) -> dict[str, Any]:
    args = getattr(params, "arguments", None) or {}
    return args if isinstance(args, dict) else {}


def build_training_tools(django: DjangoVoiceClient, session_token: str) -> list[FunctionSchema]:
    async def _propose_instruction(params):
        args = _tool_args(params)
        try:
            result = await django.training_propose(
                session_token=session_token,
                kind="instruction",
                name=str(args.get("name") or "Training instruction"),
                body=str(args.get("instruction") or args.get("body") or ""),
                scope=str(args.get("scope") or ""),
            )
        except DjangoUnreachable as exc:
            result = {"held": False, "persisted": False, "error": str(exc)}
        await params.result_callback(result)

    async def _propose_knowledge(params):
        args = _tool_args(params)
        try:
            result = await django.training_propose(
                session_token=session_token,
                kind="knowledge",
                name=str(args.get("name") or args.get("title") or "Training fact"),
                body=str(args.get("text") or args.get("body") or ""),
                scope=str(args.get("scope") or ""),
            )
        except DjangoUnreachable as exc:
            result = {"held": False, "persisted": False, "error": str(exc)}
        await params.result_callback(result)

    async def _confirm(params):
        try:
            result = await django.training_confirm(session_token=session_token)
        except DjangoUnreachable as exc:
            result = {"persisted": False, "error": str(exc)}
        await params.result_callback(result)

    return [
        FunctionSchema(
            name="propose_instruction",
            description=(
                "Hold a behavior instruction for confirmation. Does not save yet. "
                "Call this before asking the developer to confirm."
            ),
            properties={
                "name": {"type": "string", "description": "Short label for the instruction"},
                "instruction": {"type": "string", "description": "The behavior rule to save"},
                "scope": {
                    "type": "string",
                    "enum": ["global", "agent"],
                    "description": "global = every agent; agent = this agent only",
                },
            },
            required=["name", "instruction"],
            handler=_propose_instruction,
        ),
        FunctionSchema(
            name="propose_knowledge",
            description=(
                "Hold a factual knowledge item for confirmation. Does not save yet. "
                "Call this before asking the developer to confirm."
            ),
            properties={
                "name": {"type": "string", "description": "Short title for the fact"},
                "text": {"type": "string", "description": "The factual content to save"},
                "scope": {
                    "type": "string",
                    "enum": ["global", "customer"],
                    "description": "global = all customers; customer = this agent's customer",
                },
            },
            required=["name", "text"],
            handler=_propose_knowledge,
        ),
        FunctionSchema(
            name="confirm_pending",
            description=(
                "Persist the pending instruction or knowledge after the developer "
                "explicitly says yes. Never claim a save without this returning persisted=true."
            ),
            properties={},
            required=[],
            handler=_confirm,
        ),
    ]


def _training_context(agent: dict[str, Any], tools: list[FunctionSchema]) -> LLMContext:
    prompt = (
        (agent.get("resolved_system_prompt") or agent.get("system_prompt") or "").strip()
        or "You are the Vokit developer training assistant."
    )
    greeting = (agent.get("welcome_greeting") or "").strip()
    messages: list[dict[str, str]] = [{"role": "system", "content": prompt}]
    if greeting:
        messages.append({"role": "assistant", "content": greeting})
    return LLMContext(messages, tools=ToolsSchema(standard_tools=tools))


async def run_training_pipeline(
    *,
    transport,
    config: PipecatVoiceConfig,
    django: DjangoVoiceClient,
    bootstrap: dict[str, Any],
    session_token: str,
) -> None:
    agent = bootstrap.get("agent") or {}
    providers = bootstrap.get("providers") or {}
    greeting = (agent.get("welcome_greeting") or "").strip()

    try:
        stt, tts, llm = build_pipeline_services(providers)
    except UnsupportedProviderError as exc:
        logger.error("training provider mapper failed: %s", exc)
        return

    tools = build_training_tools(django, session_token)
    register = getattr(llm, "register_function", None)
    if callable(register):
        for schema in tools:
            if schema.handler is not None:
                register(schema.name, schema.handler)

    import asyncio

    vad_analyzer, turn_analyzer = await asyncio.to_thread(
        build_vad_and_turn_analyzers,
        TRAINING_AUDIO_IN_SAMPLE_RATE,
    )
    context = _training_context(agent, tools)
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=user_aggregator_params(stt, vad_analyzer, turn_analyzer),
    )
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )
    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=TRAINING_AUDIO_IN_SAMPLE_RATE,
            audio_out_sample_rate=TRAINING_AUDIO_OUT_SAMPLE_RATE,
        ),
        enable_rtvi=False,
    )

    @transport.event_handler("on_client_connected")
    async def _on_connected(transport, client):
        if greeting:
            await worker.queue_frame(TTSSpeakFrame(text=greeting, append_to_context=False))

    @transport.event_handler("on_client_disconnected")
    async def _on_disconnected(transport, client):
        await worker.cancel()

    runner = WorkerRunner(handle_sigint=False)
    try:
        await runner.add_workers(worker)
        await runner.run()
    finally:
        try:
            await django.training_end(session_token=session_token)
        except DjangoUnreachable:
            logger.warning("django unreachable at training end")
