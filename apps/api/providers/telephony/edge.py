from __future__ import annotations

import json
import urllib.error
import urllib.request

from control_plane.telephony.application.edge import EdgeCall
from control_plane.telephony.domain.call_types import TransferStatus
from shared_kernel.errors import DomainError


def _map_transfer(raw: object) -> TransferStatus:
    value = str(raw or "idle").strip().lower()
    mapping = {
        "idle": TransferStatus.IDLE,
        "pending": TransferStatus.PENDING,
        "in_progress": TransferStatus.PENDING,
        "succeeded": TransferStatus.COMPLETED,
        "completed": TransferStatus.COMPLETED,
        "failed": TransferStatus.FAILED,
    }
    return mapping.get(value, TransferStatus.IDLE)


class HttpSipEdge:
    def __init__(self, base_url: str, timeout_seconds: float = 8.0) -> None:
        self._base = (base_url or "").rstrip("/")
        self._timeout = timeout_seconds

    def originate(self, *, from_e164: str, to_e164: str) -> EdgeCall:
        body = self._request(
            "POST",
            "/v1/calls",
            {"to": to_e164, "from": from_e164},
            expected=(201, 200),
        )
        return self._call(body)

    def transfer(self, *, edge_call_id: str, to: str, timeout_seconds: int) -> EdgeCall:
        self._request(
            "POST",
            f"/v1/calls/{edge_call_id}/transfer",
            {"to": to, "max_timeout_seconds": timeout_seconds},
            expected=(202, 200),
        )
        return EdgeCall(
            edge_call_id=edge_call_id,
            status="in_progress",
            transfer_status=TransferStatus.PENDING,
        )

    def get_call(self, *, edge_call_id: str) -> EdgeCall | None:
        try:
            body = self._request("GET", f"/v1/calls/{edge_call_id}", None, expected=(200,))
        except DomainError as exc:
            if exc.code == "not_found":
                return None
            raise
        return self._call(body)

    def _call(self, body: dict) -> EdgeCall:
        call = body.get("call") if type(body.get("call")) is dict else body
        transfer = call.get("transfer") if type(call.get("transfer")) is dict else {}
        return EdgeCall(
            edge_call_id=str(call.get("id") or call.get("edge_call_id") or ""),
            status=str(call.get("status") or "unknown"),
            transfer_status=_map_transfer(transfer.get("status")),
            transfer_reason=str(transfer.get("reason") or ""),
        )

    def _request(
        self,
        method: str,
        path: str,
        payload: dict | None,
        *,
        expected: tuple[int, ...],
    ) -> dict:
        if not self._base:
            raise DomainError(
                "edge_unavailable",
                "SIP Edge is not configured.",
                http_status=503,
            )
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                status = int(response.status)
                raw = response.read().decode("utf-8") or "{}"
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise DomainError("not_found", "Resource not found.", http_status=404) from exc
            raise DomainError(
                "edge_unavailable",
                "SIP Edge request failed.",
                http_status=503,
            ) from exc
        except urllib.error.URLError as exc:
            raise DomainError(
                "edge_unavailable",
                "SIP Edge is unreachable.",
                http_status=503,
            ) from exc
        if status not in expected:
            raise DomainError(
                "edge_unavailable",
                "SIP Edge returned an unexpected status.",
                http_status=503,
            )
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DomainError(
                "edge_unavailable",
                "SIP Edge returned non-JSON.",
                http_status=503,
            ) from exc
        return parsed if type(parsed) is dict else {}
