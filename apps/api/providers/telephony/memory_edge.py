from __future__ import annotations

import uuid

from control_plane.telephony.application.edge import EdgeCall
from control_plane.telephony.domain.call_types import TransferStatus
from shared_kernel.errors import DomainError


class MemorySipEdge:
    """In-process Edge for lab tests. Completes transfers unless `to` is a fail target."""

    FAIL_TO = "+15550009999"

    def __init__(self) -> None:
        self._calls: dict[str, EdgeCall] = {}

    def reset(self) -> None:
        self._calls.clear()

    def originate(self, *, from_e164: str, to_e164: str) -> EdgeCall:
        if not from_e164 or not to_e164:
            raise DomainError("validation_error", "from and to are required.")
        edge_call_id = f"edge-out-{uuid.uuid4()}"
        call = EdgeCall(edge_call_id=edge_call_id, status="ringing")
        self._calls[edge_call_id] = call
        return call

    def transfer(self, *, edge_call_id: str, to: str, timeout_seconds: int) -> EdgeCall:
        existing = self._calls.get(edge_call_id)
        if existing is None:
            existing = EdgeCall(edge_call_id=edge_call_id, status="in_progress")
        if to == self.FAIL_TO:
            updated = EdgeCall(
                edge_call_id=edge_call_id,
                status=existing.status,
                transfer_status=TransferStatus.FAILED,
                transfer_reason="no_answer",
            )
        else:
            updated = EdgeCall(
                edge_call_id=edge_call_id,
                status=existing.status,
                transfer_status=TransferStatus.PENDING,
                transfer_reason="",
            )
        self._calls[edge_call_id] = updated
        _ = timeout_seconds
        return updated

    def get_call(self, *, edge_call_id: str) -> EdgeCall | None:
        call = self._calls.get(edge_call_id)
        if call is None:
            return None
        if call.transfer_status is TransferStatus.PENDING:
            completed = EdgeCall(
                edge_call_id=call.edge_call_id,
                status=call.status,
                transfer_status=TransferStatus.COMPLETED,
                transfer_reason="transferred",
            )
            self._calls[edge_call_id] = completed
            return completed
        return call

    def seed(self, call: EdgeCall) -> None:
        self._calls[call.edge_call_id] = call
