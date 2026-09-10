from __future__ import annotations

from dataclasses import dataclass, field

from control_plane.integrations.domain.policies import assert_action_arguments
from control_plane.integrations.domain.types import ProviderKind
from shared_kernel.ids import new_uuid7


@dataclass
class AdapterInvocation:
    provider: str
    action: str
    customer_id: str
    arguments: dict[str, object]


class MemoryIntegrationAdapter:
    """Lab CRM/accounting/automation adapter. No third-party I/O, no raw secrets."""

    def __init__(self) -> None:
        self.calls: list[AdapterInvocation] = []

    def reset(self) -> None:
        self.calls.clear()

    def execute(
        self,
        *,
        provider: ProviderKind,
        action: str,
        customer_id: str,
        arguments: dict,
        credential: str,
    ) -> dict[str, object]:
        if not credential:
            return {"ok": False, "error": "connection_required"}
        payload = assert_action_arguments(action, arguments)
        self.calls.append(
            AdapterInvocation(
                provider=provider.value,
                action=action,
                customer_id=customer_id,
                arguments=payload,
            )
        )
        return {
            "ok": True,
            "provider": provider.value,
            "action": action,
            "result": {"id": str(new_uuid7()), "status": "accepted"},
        }


@dataclass
class MemoryWebhookTransport:
    fail: bool = False
    status_code: int = 200
    sent: list[dict[str, object]] = field(default_factory=list)

    def reset(self) -> None:
        self.fail = False
        self.status_code = 200
        self.sent.clear()

    def post(
        self, *, url: str, headers: dict[str, str], body: bytes
    ) -> tuple[int, str]:
        self.sent.append(
            {
                "url": url,
                "headers": {key: value for key, value in headers.items()},
                "body_len": len(body),
            }
        )
        if self.fail:
            return 500, "transport_error"
        return self.status_code, "ok"
