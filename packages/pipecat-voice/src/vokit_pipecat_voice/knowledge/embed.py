"""Embed a query using the bootstrap snapshot (never invent credentials)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

FASTEMBED_PROVIDER_CODE = "fastembed"
FASTEMBED_DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"

_FASTEMBED_SINGLETONS: dict[str, Any] = {}


def _text_embedding(model: str):
    from fastembed import TextEmbedding

    name = (model or "").strip() or FASTEMBED_DEFAULT_MODEL
    existing = _FASTEMBED_SINGLETONS.get(name)
    if existing is not None:
        return existing
    loaded = TextEmbedding(model_name=name)
    _FASTEMBED_SINGLETONS[name] = loaded
    return loaded


def preload_fastembed_model(model: str = FASTEMBED_DEFAULT_MODEL) -> None:
    """Load ONNX weights and run one dummy query so the first call stays inside 80 ms."""
    engine = _text_embedding(model)
    list(engine.query_embed("warmup"))


def _fastembed_query_sync(text: str, model: str) -> list[float] | None:
    engine = _text_embedding(model)
    rows = list(engine.query_embed(text))
    if not rows:
        return None
    return [float(v) for v in rows[0]]


async def embed_query(text: str, embedding: dict[str, Any], *, timeout: float) -> list[float] | None:
    if not text.strip() or not embedding:
        return None
    code = (embedding.get("provider_code") or "").strip()
    model = (embedding.get("model") or "").strip()
    api_key = (embedding.get("api_key") or "").strip()
    if code == FASTEMBED_PROVIDER_CODE:
        resolved = model or FASTEMBED_DEFAULT_MODEL
        try:
            return await asyncio.to_thread(_fastembed_query_sync, text, resolved)
        except Exception:  # noqa: BLE001 — miss path continues without knowledge
            logger.warning("query embedding failed provider=%s", code)
            return None
    if not model or not api_key:
        return None
    try:
        if code == "google":
            return await _google_embed(text, model=model, api_key=api_key, timeout=timeout)
        return await _openai_embed(
            text,
            model=model,
            api_key=api_key,
            timeout=timeout,
            base_url="https://api.x.ai/v1" if code == "grok" else "https://api.openai.com/v1",
        )
    except Exception:  # noqa: BLE001 — miss path continues without knowledge
        logger.warning("query embedding failed provider=%s", code)
        return None


async def _openai_embed(
    text: str,
    *,
    model: str,
    api_key: str,
    timeout: float,
    base_url: str,
) -> list[float] | None:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/embeddings",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "input": text},
        )
    if response.status_code >= 400:
        return None
    payload = response.json()
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or not data:
        return None
    embedding = data[0].get("embedding") if isinstance(data[0], dict) else None
    if not isinstance(embedding, list):
        return None
    return [float(v) for v in embedding]


async def _google_embed(text: str, *, model: str, api_key: str, timeout: float) -> list[float] | None:
    model_id = model if model.startswith("models/") else f"models/{model}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/{model_id}:embedContent",
            params={"key": api_key},
            json={"model": model_id, "content": {"parts": [{"text": text}]}},
        )
    if response.status_code >= 400:
        return None
    payload = response.json()
    values = (
        payload.get("embedding", {}).get("values")
        if isinstance(payload, dict)
        else None
    )
    if not isinstance(values, list):
        return None
    return [float(v) for v in values]
