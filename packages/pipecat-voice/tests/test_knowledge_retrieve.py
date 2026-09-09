"""Skip-LLM decision and sealed retrieve filter (Qdrant HTTP mocked)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from vokit_pipecat_voice.knowledge.decide import should_retrieve, should_skip_llm
from vokit_pipecat_voice.knowledge.retrieve import search_tenants


def test_skip_retrieve_for_backchannels():
    assert should_retrieve("ok") is False
    assert should_retrieve("thanks") is False
    assert should_retrieve("What time do you open?") is True


def test_skip_llm_requires_factual_high_confidence_short_snippet():
    snippet = "We open at 10 AM."
    assert (
        should_skip_llm(
            skip_llm_enabled=True,
            query="What time do you open?",
            top_score=0.88,
            snippet=snippet,
            score_threshold=0.65,
        )
        is True
    )
    assert (
        should_skip_llm(
            skip_llm_enabled=True,
            query="What is the knowledge lab marker?",
            top_score=0.66,
            snippet="The knowledge lab marker is cedar-consult-2026.",
            score_threshold=0.65,
        )
        is True
    )
    assert (
        should_skip_llm(
            skip_llm_enabled=True,
            query="What is the knowledge lab marker?",
            top_score=0.64,
            snippet="The knowledge lab marker is cedar-consult-2026.",
            score_threshold=0.65,
        )
        is False
    )
    assert (
        should_skip_llm(
            skip_llm_enabled=False,
            query="What time do you open?",
            top_score=0.88,
            snippet=snippet,
            score_threshold=0.75,
        )
        is False
    )
    assert (
        should_skip_llm(
            skip_llm_enabled=True,
            query="Should I book a table for six people tomorrow night?",
            top_score=0.99,
            snippet=snippet,
            score_threshold=0.75,
        )
        is False
    )
    assert (
        should_skip_llm(
            skip_llm_enabled=True,
            query="What time do you open?",
            top_score=0.40,
            snippet=snippet,
            score_threshold=0.75,
        )
        is False
    )


@pytest.mark.asyncio
async def test_parallel_tenant_queries_never_search_without_sealed_ids():
    hits = await search_tenants(
        qdrant_url="http://127.0.0.1:6333",
        collection="vokit_knowledge",
        group_ids=[],
        vector=[0.1, 0.2],
        top_k=3,
        timeout=0.08,
    )
    assert hits == []


@pytest.mark.asyncio
async def test_merge_top_hits_from_two_tenant_queries():
    class _Resp:
        def __init__(self, rows):
            self.status_code = 200
            self._rows = rows

        def json(self):
            return {"result": self._rows}

    async def _post(url, json, timeout=None):
        group = json["filter"]["must"][0]["match"]["value"]
        assert group in {"global", "customer:12"}
        assert "customer:99" not in group
        if group == "global":
            return _Resp(
                [{"score": 0.7, "payload": {"text": "global fact", "group_id": "global"}}]
            )
        return _Resp(
            [
                {
                    "score": 0.91,
                    "payload": {"text": "customer fact", "speak_text": "short fact", "group_id": "customer:12"},
                }
            ]
        )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=_post)

    with patch("vokit_pipecat_voice.knowledge.retrieve._http_client", return_value=mock_client):
        hits = await search_tenants(
            qdrant_url="http://127.0.0.1:6333",
            collection="vokit_knowledge",
            group_ids=["global", "customer:12"],
            vector=[0.1, 0.2],
            top_k=3,
            timeout=0.08,
        )
    assert hits[0]["text"] == "customer fact"
    assert hits[0]["speak_text"] == "short fact"
    assert hits[1]["text"] == "global fact"


def test_set_messages_uses_llm_context_setter():
    from types import SimpleNamespace

    from vokit_pipecat_voice.knowledge.processor import _set_messages

    stored = [{"role": "system", "content": "old"}]

    class _Ctx:
        def set_messages(self, messages):
            stored[:] = messages

        @property
        def messages(self):
            raise AssertionError("must not assign to messages")

    frame = SimpleNamespace(context=_Ctx())
    _set_messages(frame, [{"role": "user", "content": "hi"}])
    assert stored == [{"role": "user", "content": "hi"}]


def test_training_tools_and_sample_rates_are_browser_not_phone():
    from vokit_pipecat_voice.pipeline.training import (
        TRAINING_AUDIO_IN_SAMPLE_RATE,
        TRAINING_AUDIO_OUT_SAMPLE_RATE,
        build_training_tools,
    )

    assert TRAINING_AUDIO_IN_SAMPLE_RATE == 16000
    assert TRAINING_AUDIO_OUT_SAMPLE_RATE == 24000
    django = AsyncMock()
    schemas = build_training_tools(django, "tok")
    assert [s.name for s in schemas] == [
        "propose_instruction",
        "propose_knowledge",
        "confirm_pending",
    ]
    assert all(s.handler is not None for s in schemas)


@pytest.mark.asyncio
async def test_fastembed_query_embed_does_not_call_openai():
    from vokit_pipecat_voice.knowledge.embed import embed_query

    with patch("vokit_pipecat_voice.knowledge.embed._openai_embed", new_callable=AsyncMock) as openai:
        with patch(
            "vokit_pipecat_voice.knowledge.embed._fastembed_query_sync",
            return_value=[0.2] * 384,
        ):
            vector = await embed_query(
                "What is the knowledge lab marker?",
                {
                    "provider_code": "fastembed",
                    "model": "BAAI/bge-small-en-v1.5",
                    "api_key": "",
                },
                timeout=0.08,
            )
    assert vector == [0.2] * 384
    openai.assert_not_called()


def test_skip_path_tts_cache_roundtrip():
    from vokit_pipecat_voice.knowledge.tts_cache import (
        CachedClip,
        cache_key,
        clear_clips,
        get_clip,
        put_clip,
    )

    clear_clips()
    key = cache_key("voice-a", "The marker is cedar-consult-2026.")
    put_clip(key, CachedClip(audio=b"\x00\x01", sample_rate=24000, num_channels=1))
    hit = get_clip(key)
    assert hit is not None
    assert hit.audio == b"\x00\x01"
    assert get_clip(cache_key("voice-b", "The marker is cedar-consult-2026.")) is None
    clear_clips()
    assert get_clip(key) is None
