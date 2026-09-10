from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from control_plane.agents.application.ports import KnowledgePoint
from shared_kernel.errors import DomainError


class HashEmbedding:
    dims = 8

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256((text or "").encode("utf-8")).digest()
        return [byte / 255.0 for byte in digest[: self.dims]]


@dataclass
class MemoryVectorStore:
    points: dict[str, KnowledgePoint] = field(default_factory=dict)

    def upsert(self, points: list[KnowledgePoint]) -> None:
        for point in points:
            self._assert_group(point)
            self.points[point.point_id] = point

    def delete_source(self, source_id: str) -> None:
        doomed = [key for key, row in self.points.items() if row.source_id == source_id]
        for key in doomed:
            self.points.pop(key, None)

    def search(self, group_ids: list[str], vector: list[float], top_k: int = 5) -> list[dict]:
        allowed = set(group_ids)
        hits = []
        for point in self.points.values():
            if point.group_id not in allowed or not point.is_active:
                continue
            score = _dot(point.vector, vector)
            hits.append(
                {
                    "score": score,
                    "text": point.text,
                    "group_id": point.group_id,
                    "document_id": point.document_id,
                    "chunk_id": point.chunk_id,
                    "speak_text": point.speak_text,
                    "tenant_id": point.tenant_id,
                }
            )
        hits.sort(key=lambda row: float(row["score"]), reverse=True)
        return hits[:top_k]

    def _assert_group(self, point: KnowledgePoint) -> None:
        if point.group_id == "global":
            return
        if point.group_id.startswith("agency:") and point.tenant_id:
            if point.group_id != f"agency:{point.tenant_id}":
                raise DomainError("knowledge_isolation", "group_id does not match tenant.")
            return
        if point.group_id.startswith("customer:") and point.customer_id:
            if point.group_id != f"customer:{point.customer_id}":
                raise DomainError("knowledge_isolation", "group_id does not match customer.")
            return
        if point.group_id.startswith("agent:") and point.agent_id:
            if point.group_id != f"agent:{point.agent_id}":
                raise DomainError("knowledge_isolation", "group_id does not match agent.")
            return
        raise DomainError("knowledge_isolation", "group_id is not sealed.")


class QdrantHttpStore:
    def __init__(self, url: str, collection: str, dims: int = 8) -> None:
        self._url = url.rstrip("/")
        self._collection = collection
        self._dims = dims
        self._ensured = False

    def upsert(self, points: list[KnowledgePoint]) -> None:
        if not points:
            return
        self._ensure()
        body = {
            "points": [
                {
                    "id": point.point_id,
                    "vector": point.vector,
                    "payload": {
                        "group_id": point.group_id,
                        "tenant_id": point.tenant_id,
                        "customer_id": point.customer_id,
                        "agent_id": point.agent_id,
                        "source_id": point.source_id,
                        "document_id": point.document_id,
                        "chunk_id": point.chunk_id,
                        "text": point.text,
                        "speak_text": point.speak_text,
                        "is_active": point.is_active,
                    },
                }
                for point in points
            ]
        }
        self._request("PUT", f"/collections/{self._collection}/points?wait=true", body)

    def delete_source(self, source_id: str) -> None:
        self._ensure()
        self._request(
            "POST",
            f"/collections/{self._collection}/points/delete",
            {"filter": {"must": [{"key": "source_id", "match": {"value": source_id}}]}},
        )

    def search(self, group_ids: list[str], vector: list[float], top_k: int = 5) -> list[dict]:
        self._ensure()
        hits: list[dict] = []
        for group_id in group_ids:
            body = {
                "vector": vector,
                "limit": top_k,
                "with_payload": True,
                "filter": {
                    "must": [
                        {"key": "group_id", "match": {"value": group_id}},
                        {"key": "is_active", "match": {"value": True}},
                    ]
                },
            }
            payload = self._request(
                "POST", f"/collections/{self._collection}/points/search", body
            )
            rows = payload.get("result") if isinstance(payload, dict) else []
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                data = row.get("payload") if isinstance(row.get("payload"), dict) else {}
                hits.append(
                    {
                        "score": float(row.get("score") or 0),
                        "text": str(data.get("text") or ""),
                        "group_id": str(data.get("group_id") or group_id),
                        "document_id": data.get("document_id"),
                        "chunk_id": data.get("chunk_id"),
                        "speak_text": str(data.get("speak_text") or ""),
                    }
                )
        hits.sort(key=lambda row: float(row["score"]), reverse=True)
        return hits[:top_k]

    def _ensure(self) -> None:
        if self._ensured:
            return
        self._request(
            "PUT",
            f"/collections/{self._collection}",
            {"vectors": {"size": self._dims, "distance": "Cosine"}},
            ignore_conflict=True,
        )
        self._ensured = True

    def _request(
        self, method: str, path: str, body: dict, *, ignore_conflict: bool = False
    ) -> dict:
        raw = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{self._url}{path}",
            data=raw,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = response.read().decode("utf-8") or "{}"
        except urllib.error.HTTPError as exc:
            if ignore_conflict and exc.code in {400, 409}:
                return {}
            raise DomainError(
                "knowledge_store_unavailable",
                "Knowledge store write failed.",
            ) from exc
        except urllib.error.URLError as exc:
            raise DomainError(
                "knowledge_store_unavailable",
                "Knowledge store write failed.",
            ) from exc
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))
