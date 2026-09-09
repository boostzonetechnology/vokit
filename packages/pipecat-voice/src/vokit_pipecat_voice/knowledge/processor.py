"""Insert between user aggregator and LLM. Never invent group_id. Never write Qdrant."""
from __future__ import annotations

import logging
from typing import Any

from pipecat.frames.frames import Frame, TTSSpeakFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from vokit_pipecat_voice.knowledge.decide import (
    KNOWLEDGE_MARKER,
    should_retrieve,
    should_skip_llm,
)
from vokit_pipecat_voice.knowledge.embed import embed_query
from vokit_pipecat_voice.knowledge.retrieve import search_tenants

logger = logging.getLogger(__name__)


class KnowledgeRetrieveProcessor(FrameProcessor):
    def __init__(
        self,
        *,
        knowledge: dict[str, Any],
        embedding: dict[str, Any] | None,
        qdrant_url: str,
    ) -> None:
        super().__init__()
        self._knowledge = knowledge or {}
        self._embedding = embedding or {}
        self._qdrant_url = (qdrant_url or "").strip()

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if direction != FrameDirection.DOWNSTREAM or not self._is_llm_context_frame(frame):
            await self.push_frame(frame, direction)
            return

        spec = self._knowledge
        if not spec.get("enabled"):
            await self.push_frame(frame, direction)
            return

        query = _last_user_text(frame)
        if not query or not should_retrieve(query):
            try:
                _strip_knowledge_messages(frame)
            except Exception:  # noqa: BLE001 — never block the LLM miss path
                logger.warning("knowledge strip failed; continuing to LLM")
            await self.push_frame(frame, direction)
            return

        timeout_ms = int(spec.get("retrieve_timeout_ms") or 400)
        total_timeout = max(0.05, timeout_ms / 1000.0)
        # Reserve half the budget for the Qdrant HTTP call; the other half covers
        # local FastEmbed CPU inference (asyncio.to_thread) which is not bounded
        # by the httpx timeout.
        qdrant_timeout = max(0.05, total_timeout / 2.0)
        group_ids = [str(g) for g in (spec.get("group_ids") or []) if str(g).strip()]
        if not group_ids or not self._qdrant_url or not self._embedding:
            await self.push_frame(frame, direction)
            return

        import asyncio
        import time

        started = time.perf_counter()
        try:
            hits = await asyncio.wait_for(
                self._embed_and_search(query, spec, group_ids, qdrant_timeout),
                timeout=total_timeout,
            )
        except Exception as exc:  # noqa: BLE001 — miss path is today's STT→LLM→TTS
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.warning(
                "knowledge retrieve timed out or failed after %.0f ms (%s); continuing without snippets",
                elapsed_ms,
                type(exc).__name__,
            )
            await self.push_frame(frame, direction)
            return
        logger.debug(
            "knowledge retrieve finished in %.0f ms hits=%s",
            (time.perf_counter() - started) * 1000,
            len(hits),
        )

        if not hits:
            try:
                _strip_knowledge_messages(frame)
            except Exception:  # noqa: BLE001 — never block the LLM miss path
                logger.warning("knowledge strip failed; continuing to LLM")
            await self.push_frame(frame, direction)
            return

        top = hits[0]
        snippet = (top.get("text") or "").strip()
        speak = (top.get("speak_text") or "").strip()
        skip_body = speak or snippet
        score = float(top.get("score") or 0)
        threshold = float(spec.get("score_threshold") or 0.65)
        if should_skip_llm(
            skip_llm_enabled=bool(spec.get("skip_llm_enabled")),
            query=query,
            top_score=score,
            snippet=skip_body,
            score_threshold=threshold,
        ):
            logger.info(
                "knowledge skip-LLM score=%.3f chars=%s",
                score,
                len(skip_body),
            )
            await self.push_frame(
                TTSSpeakFrame(text=skip_body, append_to_context=True),
                direction,
            )
            return

        inject_threshold = min(threshold, 0.45)
        usable = [h for h in hits if float(h.get("score") or 0) >= inject_threshold and (h.get("text") or "").strip()]
        try:
            _inject_snippets(frame, [str(h["text"]).strip() for h in usable[: int(spec.get("top_k") or 3)]])
        except Exception:  # noqa: BLE001 — miss path is today's STT→LLM→TTS
            logger.warning("knowledge inject failed; continuing to LLM")
        await self.push_frame(frame, direction)

    async def _embed_and_search(
        self,
        query: str,
        spec: dict[str, Any],
        group_ids: list[str],
        timeout: float,
    ) -> list[dict[str, Any]]:
        vector = await embed_query(query, self._embedding, timeout=timeout)
        if not vector:
            return []
        return await search_tenants(
            qdrant_url=self._qdrant_url,
            collection=str(spec.get("collection") or "vokit_knowledge"),
            group_ids=group_ids,
            vector=vector,
            top_k=int(spec.get("top_k") or 3),
            timeout=timeout,
        )

    def _is_llm_context_frame(self, frame: Frame) -> bool:
        name = frame.__class__.__name__
        if name in {"LLMContextFrame", "OpenAILLMContextFrame", "LLMMessagesFrame"}:
            return True
        return bool(getattr(frame, "context", None) or getattr(frame, "messages", None))


def _messages_from(frame: Frame) -> list | None:
    context = getattr(frame, "context", None)
    if context is not None:
        getter = getattr(context, "get_messages", None)
        if callable(getter):
            return list(getter())
        messages = getattr(context, "messages", None)
        if isinstance(messages, list):
            return list(messages)
    messages = getattr(frame, "messages", None)
    if isinstance(messages, list):
        return list(messages)
    return None


def _set_messages(frame: Frame, messages: list) -> None:
    # Pipecat 1.7 LLMContext.messages is a read-only property; use set_messages().
    context = getattr(frame, "context", None)
    if context is not None:
        setter = getattr(context, "set_messages", None)
        if callable(setter):
            setter(messages)
            return
    existing = getattr(frame, "messages", None)
    if isinstance(existing, list):
        existing[:] = messages
        return
    setter = getattr(frame, "set_messages", None)
    if callable(setter):
        setter(messages)


def _last_user_text(frame: Frame) -> str:
    messages = _messages_from(frame) or []
    for message in reversed(messages):
        role, content = _role_content(message)
        if role == "user" and content and not content.startswith(KNOWLEDGE_MARKER):
            return content
    return ""


def _role_content(message) -> tuple[str, str]:
    if isinstance(message, dict):
        role = str(message.get("role") or "")
        content = message.get("content") or ""
        if not isinstance(content, str):
            content = str(content)
        return role, content
    role = str(getattr(message, "role", "") or "")
    content = getattr(message, "content", "") or ""
    if not isinstance(content, str):
        content = str(content)
    return role, content


def _strip_knowledge_messages(frame: Frame) -> None:
    messages = _messages_from(frame)
    if not messages:
        return
    kept = []
    for message in messages:
        _role, content = _role_content(message)
        if content.startswith(KNOWLEDGE_MARKER):
            continue
        kept.append(message)
    if len(kept) != len(messages):
        _set_messages(frame, kept)


def _inject_snippets(frame: Frame, snippets: list[str]) -> None:
    _strip_knowledge_messages(frame)
    if not snippets:
        return
    body = KNOWLEDGE_MARKER + "\n" + "\n".join(f"- {s}" for s in snippets)
    messages = _messages_from(frame) or []
    insert_at = len(messages)
    for index in range(len(messages) - 1, -1, -1):
        role, _content = _role_content(messages[index])
        if role == "user":
            insert_at = index
            break
    messages.insert(insert_at, {"role": "system", "content": body})
    _set_messages(frame, messages)
