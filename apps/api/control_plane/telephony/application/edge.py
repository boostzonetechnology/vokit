from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from control_plane.telephony.domain.call_types import TransferStatus


@dataclass(frozen=True, slots=True)
class EdgeCall:
    edge_call_id: str
    status: str
    transfer_status: TransferStatus = TransferStatus.IDLE
    transfer_reason: str = ""


class SipEdgeControl(Protocol):
    def originate(self, *, from_e164: str, to_e164: str) -> EdgeCall: ...

    def transfer(
        self, *, edge_call_id: str, to: str, timeout_seconds: int
    ) -> EdgeCall: ...

    def get_call(self, *, edge_call_id: str) -> EdgeCall | None: ...
