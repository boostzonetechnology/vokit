"""Pipecat → Qdrant search using Django-sealed group_ids only."""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_CLIENT: httpx.AsyncClient | None = None


def _http_client() -> httpx.AsyncClient:
    """Reuse one client. A new TCP connect to Docker Qdrant on Windows is ~1s."""
    global _CLIENT
    if _CLIENT is None or _CLIENT.is_closed:
        _CLIENT = httpx.AsyncClient(
            timeout=httpx.Timeout(2.0, connect=2.0),
            limits=httpx.Limits(max_keepalive_connections=4, max_connections=8),
        )
    return _CLIENT


async def warmup_qdrant(qdrant_url: str) -> None:
    """Open the keep-alive socket at process start so the first retrieve stays in budget."""
    base = (qdrant_url or "").strip().rstrip("/")
    if not base:
        return
    await _http_client().get(f"{base}/")


async def search_tenants(
    *,
    qdrant_url: str,
    collection: str,
    group_ids: list[str],
    vector: list[float],
    top_k: int,
    timeout: float,
) -> list[dict[str, Any]]:
    """Two tenant queries (official is_tenant), then merge top_k by score.

    Queries run sequentially on one keep-alive client. Parallel POSTs open a
    second TCP socket; on Windows Docker Desktop that connect is ~1s and
    always misses the 80 ms budget.
    """
    if not qdrant_url or not vector or not group_ids:
        return []
    base = qdrant_url.rstrip("/")
    hits: list[dict[str, Any]] = []
    for group_id in group_ids:
        try:
            hits.extend(
                await _search_one(
                    base=base,
                    collection=collection,
                    group_id=group_id,
                    vector=vector,
                    top_k=top_k,
                    timeout=timeout,
                )
            )
        except Exception as exc:  # noqa: BLE001 — miss one tenant, keep the other
            logger.warning("qdrant tenant query failed: %s", exc)
    hits.sort(key=lambda row: float(row.get("score") or 0), reverse=True)
    return hits[:top_k]


async def _search_one(
    *,
    base: str,
    collection: str,
    group_id: str,
    vector: list[float],
    top_k: int,
    timeout: float,
) -> list[dict[str, Any]]:
    payload = {
        "vector": vector,
        "limit": top_k,
        "with_payload": True,
        "with_vector": False,
        "filter": {
            "must": [
                {"key": "group_id", "match": {"value": group_id}},
                {"key": "is_active", "match": {"value": True}},
            ]
        },
    }
    response = await _http_client().post(
        f"{base}/collections/{collection}/points/search",
        json=payload,
        timeout=timeout,
    )
    if response.status_code >= 400:
        logger.warning("qdrant search HTTP %s group_id=%s", response.status_code, group_id)
        return []
    body = response.json()
    rows = body.get("result") if isinstance(body, dict) else None
    if not isinstance(rows, list):
        return []
    hits: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        point_payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        hits.append(
            {
                "score": float(row.get("score") or 0),
                "text": str(point_payload.get("text") or ""),
                "group_id": str(point_payload.get("group_id") or group_id),
                "document_id": point_payload.get("document_id"),
                "chunk_id": point_payload.get("chunk_id"),
                "speak_text": str(point_payload.get("speak_text") or ""),
            }
        )
    return hits
