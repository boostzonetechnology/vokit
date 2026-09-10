from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, replace
from typing import Protocol

from control_plane.agents.application.ports import GlobalInstructionRepository
from control_plane.agents.application.resolve import resolve_for_agent
from control_plane.agents.domain.policies import (
    assert_no_secrets,
    assert_production_routable,
    assert_test_routable,
)
from control_plane.agents.domain.types import ALLOWED_TOOLS, TestSessionStatus
from control_plane.billing.application.ports import (
    BillingIdempotencyRepository,
    IdempotencyRecord,
    PlanVersionRepository,
)
from control_plane.billing.domain.lots import LotBalance, drain_lots, remaining_minutes
from control_plane.billing.domain.types import LotKind
from control_plane.customers.domain.types import CustomerStatus
from control_plane.ops.application.live_flags import assert_calling_live, calling_is_live
from control_plane.risk.application.gate import CustomerRiskGate
from control_plane.telephony.application.edge import SipEdgeControl
from control_plane.telephony.application.ports import PhoneNumberRecord, PhoneNumberRepository
from control_plane.telephony.domain.admission import (
    admit_usage,
    decide_continue,
    normalize_did,
)
from control_plane.telephony.domain.call_types import (
    CallDirection,
    CallStatus,
    TransferStatus,
)
from control_plane.telephony.domain.destinations import (
    AfterHoursAction,
    DestinationKind,
    DestinationStatus,
    after_hours_action,
    hunt_target,
    is_within_hours,
    parse_hours,
)
from control_plane.telephony.domain.types import NumberStatus
from control_plane.telephony.domain.voicemail import (
    VoicemailAction,
    assert_voicemail_action,
    assert_voicemail_direction,
    next_voicemail_status,
)
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.agents.service import TenantAgentService
from tenant.billing.domain import MinuteLotRecord
from tenant.billing.service import TenantBillingService
from tenant.calls.domain import TenantCallEventRecord, TenantCallRecord
from tenant.calls.service import TenantCallService
from tenant.lifecycle.service import TenantLifecycleService
from tenant.media.domain import VoicemailMessageRecord
from tenant.media.service import TenantMediaService

logger = logging.getLogger("vokit.voice")


@dataclass(frozen=True, slots=True)
class CallIndexRecord:
    call_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    agent_id: uuid.UUID
    edge_call_id: str
    e164: str
    direction: CallDirection
    status: CallStatus
    transfer_status: TransferStatus
    billed_minutes: int
    created_at: object = None
    ended_at: object = None
    remote_e164: str = ""
    transfer_destination_id: object = None
    voicemail_status: str = ""
    hunt_index: int = 0


@dataclass(frozen=True, slots=True)
class VoiceProviders:
    stt: dict[str, str]
    tts: dict[str, str]
    llm: dict[str, str]


class CallIndexRepository(Protocol):
    def get_by_edge(self, edge_call_id: str) -> CallIndexRecord | None: ...
    def save(self, record: CallIndexRecord) -> CallIndexRecord: ...
    def get(self, call_id: uuid.UUID) -> CallIndexRecord | None: ...
    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[CallIndexRecord]: ...


class ToolGateway(Protocol):
    def invoke(
        self, *, call: CallIndexRecord, tool: str, arguments: dict | None
    ) -> dict[str, object]: ...


class OutboundEventSink(Protocol):
    def emit(
        self,
        *,
        event_type: str,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        object_id: uuid.UUID,
        data: dict[str, object],
    ) -> None: ...


class TrainingProposalRepository(Protocol):
    def create(self, session_id: uuid.UUID, kind: str, name: str, scope: str) -> str: ...
    def confirm(self, session_id: uuid.UUID) -> int: ...


class TrainingSessionIndexRepository(Protocol):
    def save(
        self,
        *,
        session_id: uuid.UUID,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> None: ...

    def get(self, session_id: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID] | None: ...


class VoiceControl:
    def __init__(
        self,
        numbers: PhoneNumberRepository,
        agents: TenantAgentService,
        lifecycle: TenantLifecycleService,
        billing: TenantBillingService,
        versions: PlanVersionRepository,
        calls: TenantCallService,
        index: CallIndexRepository,
        proposals: TrainingProposalRepository,
        training_index: TrainingSessionIndexRepository,
        instructions: GlobalInstructionRepository,
        gate: CustomerRiskGate,
        clock: Clock,
        providers: VoiceProviders,
        media: TenantMediaService,
        dest_index,
        edge: SipEdgeControl,
        keys: BillingIdempotencyRepository,
        tools: ToolGateway | None = None,
        events: OutboundEventSink | None = None,
    ) -> None:
        self._numbers = numbers
        self._agents = agents
        self._lifecycle = lifecycle
        self._billing = billing
        self._versions = versions
        self._calls = calls
        self._index = index
        self._proposals = proposals
        self._training_index = training_index
        self._instructions = instructions
        self._gate = gate
        self._clock = clock
        self._providers = providers
        self._media = media
        self._dest_index = dest_index
        self._edge = edge
        self._keys = keys
        self._tools = tools
        self._events = events

    def resolve_did(self, did: str) -> dict[str, object]:
        if not calling_is_live():
            return {"routable": False, "reason": "calling_not_live"}
        try:
            decision = self._admit(did)
        except DomainError as exc:
            if exc.code == "invalid_phone":
                return {"routable": False, "reason": "invalid_did"}
            raise
        return {
            "routable": decision["reason"] is None,
            "reason": decision["reason"] or "ok",
        }

    def bootstrap(
        self,
        *,
        did: str,
        edge_call_id: str,
        from_number: str,
        sip_call_id: str,
        direction: str,
    ) -> dict[str, object]:
        if not calling_is_live():
            return {"admitted": False, "reject_reason": "calling_not_live"}
        edge = (edge_call_id or "").strip()
        if not edge:
            return {"admitted": False, "reject_reason": "missing_edge_call_id"}
        existing = self._index.get_by_edge(edge)
        if existing is not None:
            if existing.status is CallStatus.RINGING:
                existing = self._mark_in_progress(existing)
            return self._snapshot(existing, admitted=True)
        try:
            decision = self._admit(did)
        except DomainError as exc:
            if exc.code == "invalid_phone":
                return {"admitted": False, "reject_reason": "invalid_did", "edge_call_id": edge}
            raise
        if decision["reason"] is not None:
            return {
                "admitted": False,
                "reject_reason": decision["reason"],
                "edge_call_id": edge,
            }
        now = self._clock.now()
        number: PhoneNumberRecord = decision["number"]
        agent = decision["agent"]
        try:
            parsed_direction = CallDirection((direction or "inbound").strip().lower())
        except ValueError:
            parsed_direction = CallDirection.INBOUND
        call_id = new_uuid7()
        self._calls.put_call(
            agent.tenant_id,
            TenantCallRecord(
                call_id=call_id,
                tenant_id=agent.tenant_id,
                customer_id=agent.customer_id,
                agent_id=agent.agent_id,
                phone_number_id=number.id,
                e164=number.e164,
                edge_call_id=edge,
                sip_call_id=(sip_call_id or "").strip(),
                direction=parsed_direction,
                status=CallStatus.IN_PROGRESS,
                billed_minutes=0,
                duration_seconds=0,
                end_reason="",
                started_at=now,
                remote_e164=(from_number or "").strip(),
            ),
        )
        indexed = self._index.save(
            CallIndexRecord(
                call_id=call_id,
                tenant_id=agent.tenant_id,
                customer_id=agent.customer_id,
                agent_id=agent.agent_id,
                edge_call_id=edge,
                e164=number.e164,
                direction=parsed_direction,
                status=CallStatus.IN_PROGRESS,
                transfer_status=TransferStatus.IDLE,
                billed_minutes=0,
                created_at=now,
                remote_e164=(from_number or "").strip(),
            )
        )
        log_event(
            logger,
            "voice.session.bootstrapped",
            outcome="success",
            tenant_id=str(agent.tenant_id),
            customer_id=str(agent.customer_id),
            agent_id=str(agent.agent_id),
            call_id=str(call_id),
        )
        return self._snapshot(indexed, admitted=True, from_number=from_number)

    def record_event(
        self, *, edge_call_id: str, event_type: str, role: str = "", reason: str = ""
    ) -> dict[str, object]:
        indexed = self._require_call(edge_call_id)
        now = self._clock.now()
        self._calls.put_event(
            indexed.tenant_id,
            TenantCallEventRecord(
                event_id=new_uuid7(),
                call_id=indexed.call_id,
                tenant_id=indexed.tenant_id,
                event_type=(event_type or "event").strip()[:64],
                role=(role or "").strip()[:16],
                reason=(reason or "").strip()[:64],
                created_at=now,
            )
        )
        decision = self._continue_for(indexed, now)
        return {
            "ok": True,
            "continue_call": decision.continue_call,
            "reason": decision.reason,
        }

    def continue_session(self, *, edge_call_id: str, elapsed_seconds: int = 0) -> dict:
        indexed = self._require_call(edge_call_id)
        decision = decide_continue(
            remaining_minutes=self._remaining(indexed.tenant_id, indexed.customer_id),
            elapsed_seconds=elapsed_seconds,
            overage_enabled=self._plan_flags(indexed)[0],
            grace_seconds=self._plan_flags(indexed)[1],
        )
        return {
            "continue_call": decision.continue_call,
            "reason": decision.reason,
            "remaining_minutes": decision.remaining_minutes,
            "in_grace": decision.in_grace,
            "overage": decision.overage,
        }

    def end_session(
        self, *, edge_call_id: str, reason: str = "", status: str = ""
    ) -> dict[str, object]:
        indexed = self._require_call(edge_call_id)
        now = self._clock.now()
        started = indexed.created_at or now
        elapsed = max(0, int((now - started).total_seconds()))
        billed = max(0, (elapsed + 59) // 60) if elapsed else 0
        self._drain(indexed, billed)
        try:
            final_status = CallStatus((status or "completed").strip().lower())
        except ValueError:
            final_status = CallStatus.COMPLETED
        call = self._calls.get_call(indexed.tenant_id, indexed.call_id)
        if call is not None:
            self._calls.put_call(
                indexed.tenant_id,
                replace(
                    call,
                    status=final_status,
                    billed_minutes=billed,
                    duration_seconds=elapsed,
                    end_reason=(reason or "completed").strip()[:64],
                    ended_at=now,
                ),
            )
        self._index.save(
            replace(
                indexed,
                status=final_status,
                billed_minutes=billed,
                ended_at=now,
            )
        )
        log_event(
            logger,
            "voice.session.ended",
            outcome="success",
            tenant_id=str(indexed.tenant_id),
            call_id=str(indexed.call_id),
            billed_minutes=billed,
        )
        if self._events is not None:
            try:
                self._events.emit(
                    event_type="call.completed",
                    tenant_id=indexed.tenant_id,
                    customer_id=indexed.customer_id,
                    object_id=indexed.call_id,
                    data={"status": final_status.value, "billed_minutes": billed},
                )
            except DomainError:
                log_event(
                    logger,
                    "voice.session.webhook_failed",
                    outcome="failed",
                    call_id=str(indexed.call_id),
                )
        return {
            "ok": True,
            "continue_call": False,
            "billed_minutes": billed,
            "status": final_status.value,
        }

    def originate(
        self,
        *,
        tenant_id: uuid.UUID,
        agent_id: uuid.UUID,
        to: str,
        actor_id: uuid.UUID,
        idempotency_key: str,
    ) -> dict[str, object]:
        assert_calling_live()
        key = idempotency_key.strip()
        if not key:
            raise DomainError("validation_error", "Idempotency-Key is required.")
        replay = self._keys.get(actor_id, key)
        if replay is not None:
            indexed = self._index.get(replay.resource_id)
            if indexed is not None:
                return self._originated_payload(indexed)
        dest = normalize_did(to)
        agent = self._agents.get_agent(tenant_id, agent_id)
        if agent is None or agent.tenant_id != tenant_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if not agent.outbound_enabled:
            raise DomainError(
                "outbound_disabled",
                "Outbound calling is not enabled for this agent.",
                http_status=409,
            )
        number = next(
            (
                row
                for row in self._numbers.list(tenant_id=tenant_id)
                if row.assigned_agent_id == agent.agent_id
                and row.status is NumberStatus.ASSIGNED
            ),
            None,
        )
        if number is None:
            raise DomainError(
                "number_unassigned",
                "Agent has no assigned caller ID.",
                http_status=409,
            )
        decision = self._admit(number.e164, require_inbound=False)
        if decision["reason"] is not None:
            raise DomainError(
                str(decision["reason"]),
                "Call was not admitted.",
                http_status=409,
            )
        edge = self._edge.originate(from_e164=number.e164, to_e164=dest)
        now = self._clock.now()
        call_id = new_uuid7()
        self._calls.put_call(
            tenant_id,
            TenantCallRecord(
                call_id=call_id,
                tenant_id=tenant_id,
                customer_id=agent.customer_id,
                agent_id=agent.agent_id,
                phone_number_id=number.id,
                e164=number.e164,
                edge_call_id=edge.edge_call_id,
                sip_call_id="",
                direction=CallDirection.OUTBOUND,
                status=CallStatus.RINGING,
                billed_minutes=0,
                duration_seconds=0,
                end_reason="",
                started_at=now,
                remote_e164=dest,
            ),
        )
        indexed = self._index.save(
            CallIndexRecord(
                call_id=call_id,
                tenant_id=tenant_id,
                customer_id=agent.customer_id,
                agent_id=agent.agent_id,
                edge_call_id=edge.edge_call_id,
                e164=number.e164,
                direction=CallDirection.OUTBOUND,
                status=CallStatus.RINGING,
                transfer_status=TransferStatus.IDLE,
                billed_minutes=0,
                created_at=now,
                remote_e164=dest,
            )
        )
        self._keys.create(
            IdempotencyRecord(
                actor_id=actor_id,
                key=key,
                kind="outbound_call",
                resource_id=call_id,
            )
        )
        log_event(
            logger,
            "voice.session.originated",
            outcome="success",
            tenant_id=str(tenant_id),
            call_id=str(call_id),
            edge_call_id=edge.edge_call_id,
        )
        return self._originated_payload(indexed)

    def request_transfer(
        self, *, edge_call_id: str, destination_id: str = ""
    ) -> dict[str, object]:
        indexed = self._require_call(edge_call_id)
        destination = self._pick_destination(indexed, destination_id)
        if destination is None:
            return {
                "ok": False,
                "available": False,
                "status": TransferStatus.IDLE.value,
                "reason": "not_configured",
                "continue_call": True,
            }
        override = self._dest_index.get(destination.destination_id)
        if destination.status is DestinationStatus.DISABLED or (
            override is not None and override.platform_disabled
        ):
            return {
                "ok": False,
                "available": False,
                "status": TransferStatus.IDLE.value,
                "reason": "disabled",
                "continue_call": True,
            }
        hunted = hunt_target(
            kind=destination.kind,
            target=destination.target,
            members=tuple((member.kind, member.target) for member in destination.members),
            start_index=indexed.hunt_index,
        )
        if hunted is None:
            return {
                "ok": False,
                "available": False,
                "status": TransferStatus.FAILED.value,
                "reason": "no_members",
                "continue_call": True,
            }
        edge_result = self._edge.transfer(
            edge_call_id=indexed.edge_call_id,
            to=hunted.to,
            timeout_seconds=destination.no_answer_seconds,
        )
        next_status = edge_result.transfer_status
        if next_status is TransferStatus.IDLE:
            next_status = TransferStatus.PENDING
        updated = self._index.save(
            replace(
                indexed,
                transfer_status=next_status,
                transfer_destination_id=destination.destination_id,
                hunt_index=hunted.member_index,
            )
        )
        if (
            next_status is TransferStatus.FAILED
            and destination.kind is DestinationKind.QUEUE
        ):
            nxt = hunt_target(
                kind=destination.kind,
                target=destination.target,
                members=tuple((member.kind, member.target) for member in destination.members),
                start_index=hunted.member_index + 1,
            )
            if nxt is not None:
                self._index.save(replace(updated, hunt_index=nxt.member_index))
                return self.request_transfer(
                    edge_call_id=edge_call_id,
                    destination_id=str(destination.destination_id),
                )
        log_event(
            logger,
            "voice.transfer.requested",
            outcome="success",
            tenant_id=str(updated.tenant_id),
            call_id=str(updated.call_id),
            kind=destination.kind.value,
        )
        return {
            "ok": True,
            "available": True,
            "status": TransferStatus.PENDING.value,
            "reason": "pending",
            "kind": destination.kind.value,
            "to": hunted.to,
            "continue_call": True,
        }

    def transfer_status(self, *, edge_call_id: str) -> dict[str, object]:
        indexed = self._require_call(edge_call_id)
        if indexed.transfer_status is TransferStatus.IDLE:
            return {
                "ok": False,
                "status": TransferStatus.IDLE.value,
                "reason": "not_configured",
                "continue_call": True,
            }
        edge = self._edge.get_call(edge_call_id=indexed.edge_call_id)
        status = edge.transfer_status if edge is not None else indexed.transfer_status
        reason = edge.transfer_reason if edge is not None else indexed.transfer_status.value
        if status is TransferStatus.FAILED:
            destination = None
            if indexed.transfer_destination_id:
                destination = self._media.get_destination(
                    indexed.tenant_id, indexed.transfer_destination_id
                )
            if destination is not None and destination.kind is DestinationKind.QUEUE:
                nxt = hunt_target(
                    kind=destination.kind,
                    target=destination.target,
                    members=tuple(
                        (member.kind, member.target) for member in destination.members
                    ),
                    start_index=indexed.hunt_index + 1,
                )
                if nxt is not None:
                    self._index.save(replace(indexed, hunt_index=nxt.member_index))
                    return self.request_transfer(
                        edge_call_id=edge_call_id,
                        destination_id=str(destination.destination_id),
                    )
        self._index.save(replace(indexed, transfer_status=status))
        return {
            "ok": status is TransferStatus.COMPLETED,
            "status": status.value,
            "reason": reason or status.value,
            "continue_call": status is not TransferStatus.COMPLETED,
        }

    def record_voicemail(
        self,
        *,
        edge_call_id: str,
        direction: str,
        action: str,
        duration_seconds: int = 0,
    ) -> dict[str, object]:
        indexed = self._require_call(edge_call_id)
        parsed_direction = assert_voicemail_direction(direction)
        parsed_action = assert_voicemail_action(action)
        if type(duration_seconds) is not int or duration_seconds < 0:
            raise DomainError("validation_error", "duration_seconds must be >= 0.")
        now = self._clock.now()
        existing = self._media.list_voicemail(indexed.tenant_id, call_id=indexed.call_id)
        current = existing[0] if existing else None
        status = next_voicemail_status(parsed_action)
        if parsed_action is VoicemailAction.START or current is None:
            current = VoicemailMessageRecord(
                message_id=new_uuid7(),
                tenant_id=indexed.tenant_id,
                customer_id=indexed.customer_id,
                agent_id=indexed.agent_id,
                call_id=indexed.call_id,
                direction=parsed_direction,
                status=status,
                object_ref="",
                duration_seconds=duration_seconds,
                created_at=now,
                updated_at=now,
            )
        else:
            current = replace(
                current,
                status=status,
                duration_seconds=duration_seconds or current.duration_seconds,
                updated_at=now,
            )
        stored = self._media.put_voicemail(indexed.tenant_id, current)
        self._index.save(replace(indexed, voicemail_status=stored.status.value))
        call = self._calls.get_call(indexed.tenant_id, indexed.call_id)
        if call is not None:
            self._calls.put_call(
                indexed.tenant_id,
                replace(call, voicemail_status=stored.status.value),
            )
        self._calls.put_event(
            indexed.tenant_id,
            TenantCallEventRecord(
                event_id=new_uuid7(),
                call_id=indexed.call_id,
                tenant_id=indexed.tenant_id,
                event_type="voicemail",
                role=parsed_direction.value,
                reason=stored.status.value,
                created_at=now,
            ),
        )
        log_event(
            logger,
            "voice.voicemail.recorded",
            outcome="success",
            tenant_id=str(indexed.tenant_id),
            call_id=str(indexed.call_id),
            status=stored.status.value,
        )
        return {
            "ok": True,
            "message_id": str(stored.message_id),
            "status": stored.status.value,
            "object_ref": stored.object_ref,
            "continue_call": stored.status.value == "recording",
        }

    def list_tenant_calls(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
    ) -> list[TenantCallRecord]:
        return self._calls.list_calls(tenant_id, customer_id=customer_id, agent_id=agent_id)

    def list_index_calls(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[CallIndexRecord]:
        return self._index.list(tenant_id=tenant_id, customer_id=customer_id)

    def invoke_tool(
        self, *, edge_call_id: str, tool: str, arguments: dict | None = None
    ) -> dict[str, object]:
        indexed = self._require_call(edge_call_id)
        name = (tool or "").strip()
        if name == "request_call_transfer" or name == "transfer_call":
            dest = str((arguments or {}).get("destination_id") or "")
            return self.request_transfer(edge_call_id=edge_call_id, destination_id=dest)
        if name not in ALLOWED_TOOLS:
            return {"ok": False, "error": "invalid_tool", "continue_call": True}
        if self._tools is not None:
            return self._tools.invoke(call=indexed, tool=name, arguments=arguments)
        return {"ok": False, "error": "connection_required", "continue_call": True}

    def training_bootstrap(self, *, session_token: str) -> dict[str, object]:
        session, agent = self._training_session(session_token)
        if session is None or agent is None:
            return {"admitted": False, "reject_reason": "training_not_found"}
        try:
            assert_test_routable(status=agent.status)
        except DomainError:
            return {"admitted": False, "reject_reason": "unpublished"}
        resolved = resolve_for_agent(agent, self._agents, self._instructions)
        attachments = self._agents.list_attachments(agent.tenant_id, agent.agent_id)
        return {
            "admitted": True,
            "session_token": str(session.session_id),
            "edge_call_id": str(session.session_id),
            "agent": self._agent_payload(agent, resolved),
            "providers": self._provider_payload(agent),
            "timers": {"silence_timeout_seconds": 20, "max_call_duration_seconds": 1800},
            "transfer": {"configured": False},
            "knowledge": {
                "enabled": bool(attachments),
                "group_ids": [row.group_id for row in attachments],
                "retrieve_timeout_ms": 400,
            },
        }

    def training_propose(
        self, *, session_token: str, kind: str, name: str, body: str, scope: str = ""
    ) -> dict[str, object]:
        session, _agent = self._training_session(session_token)
        if session is None:
            return {"ok": False, "reason": "training_not_found"}
        assert_no_secrets(body, field="body")
        proposal_id = self._proposals.create(
            session.session_id, kind, name, scope
        )
        return {"ok": True, "proposal_id": proposal_id, "status": "proposed"}

    def training_confirm(self, *, session_token: str) -> dict[str, object]:
        session, _agent = self._training_session(session_token)
        if session is None:
            return {"ok": False, "reason": "training_not_found"}
        count = self._proposals.confirm(session.session_id)
        return {"ok": True, "confirmed": count}

    def training_end(self, *, session_token: str) -> dict[str, object]:
        session, agent = self._training_session(session_token)
        if session is None or agent is None:
            return {"ok": False, "reason": "training_not_found"}
        self._agents.put_session(
            agent.tenant_id,
            replace(session, status=TestSessionStatus.ENDED.value, ended_at=self._clock.now()),
        )
        return {"ok": True, "status": "ended"}

    def _admit(self, did: str, *, require_inbound: bool = True) -> dict:
        e164 = normalize_did(did)
        number = self._numbers.get_by_e164(e164)
        if number is None or number.status is not NumberStatus.ASSIGNED:
            return {"reason": "number_unassigned", "number": None, "agent": None}
        if (
            number.assigned_tenant_id is None
            or number.assigned_agent_id is None
            or number.assigned_customer_id is None
        ):
            return {"reason": "number_unassigned", "number": None, "agent": None}
        agent = self._agents.get_agent(number.assigned_tenant_id, number.assigned_agent_id)
        if agent is None:
            return {"reason": "unpublished", "number": number, "agent": None}
        try:
            assert_production_routable(
                status=agent.status, published_version=agent.published_version
            )
        except DomainError as exc:
            reason = "unpublished"
            if exc.details:
                reason = str(exc.details.get("reason") or reason)
            return {"reason": reason, "number": number, "agent": agent}
        if require_inbound and not agent.inbound_enabled:
            return {"reason": "inbound_disabled", "number": number, "agent": agent}
        hours = parse_hours(list(agent.business_hours))
        open_now = is_within_hours(
            self._clock.now(), timezone_name=agent.timezone, windows=hours
        )
        hours_action = after_hours_action(
            open_now=open_now, fallback_behavior=agent.fallback_behavior
        )
        if require_inbound and hours_action is AfterHoursAction.REJECT:
            return {"reason": "outside_hours", "number": number, "agent": agent}
        customer = self._lifecycle.get_customer(agent.tenant_id, agent.customer_id)
        if customer is None or customer.status is not CustomerStatus.ACTIVE:
            return {"reason": "customer_inactive", "number": number, "agent": agent}
        try:
            self._gate.assert_open(agent.customer_id)
        except DomainError:
            return {"reason": "customer_risk_blocked", "number": number, "agent": agent}
        subscription = self._billing.get_active_subscription(agent.tenant_id, agent.customer_id)
        if subscription is None:
            return {"reason": "subscription_required", "number": number, "agent": agent}
        version = self._versions.get(subscription.plan_version_id)
        remaining = self._remaining(agent.tenant_id, agent.customer_id)
        denied = admit_usage(
            remaining_minutes=remaining,
            overage_enabled=bool(version.overage_enabled) if version else False,
            grace_seconds=int(version.grace_seconds) if version else 0,
        )
        return {
            "reason": denied,
            "number": number,
            "agent": agent,
            "after_hours": hours_action,
        }

    def _snapshot(
        self,
        indexed: CallIndexRecord,
        *,
        admitted: bool,
        from_number: str = "",
    ) -> dict[str, object]:
        agent = self._agents.get_agent(indexed.tenant_id, indexed.agent_id)
        if agent is None:
            return {
                "admitted": False,
                "reject_reason": "unpublished",
                "edge_call_id": indexed.edge_call_id,
            }
        resolved = resolve_for_agent(agent, self._agents, self._instructions)
        attachments = self._agents.list_attachments(agent.tenant_id, agent.agent_id)
        return {
            "admitted": admitted,
            "edge_call_id": indexed.edge_call_id,
            "vokit_call_id": str(indexed.call_id),
            "from_number": from_number,
            "agent": self._agent_payload(agent, resolved),
            "providers": self._provider_payload(agent),
            "timers": {
                "silence_timeout_seconds": 20,
                "max_call_duration_seconds": 1800,
            },
            "transfer": self._transfer_spec(indexed, agent),
            "voicemail": self._voicemail_spec(indexed, agent),
            "knowledge": {
                "enabled": bool(attachments),
                "group_ids": [row.group_id for row in attachments],
                "retrieve_timeout_ms": 400,
            },
            "compliance": {
                "recording_disclosure": agent.recording_disclosure,
            },
        }

    def _agent_payload(self, agent, resolved: str) -> dict[str, object]:
        assert_no_secrets(resolved, field="instructions")
        return {
            "id": str(agent.agent_id),
            "welcome_greeting": agent.greeting,
            "resolved_system_prompt": resolved,
            "language": agent.language,
            "voice_id": agent.voice_id,
            "tools": list(agent.tools),
        }

    def _provider_payload(self, agent) -> dict[str, object]:
        tts = dict(self._providers.tts)
        if agent.voice_id:
            tts["voice_id"] = agent.voice_id
        if agent.language:
            tts["language"] = agent.language
        if agent.voice_provider:
            tts["provider_code"] = agent.voice_provider
        return {
            "stt": dict(self._providers.stt),
            "tts": tts,
            "llm": dict(self._providers.llm),
        }

    def _require_call(self, edge_call_id: str) -> CallIndexRecord:
        indexed = self._index.get_by_edge((edge_call_id or "").strip())
        if indexed is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return indexed

    def _remaining(self, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> int:
        lots = self._billing.list_lots(tenant_id, customer_id)
        balances = tuple(
            LotBalance(
                lot_id=str(lot.lot_id),
                kind=lot.kind,
                remaining_minutes=lot.remaining_minutes,
            )
            for lot in lots
        )
        return remaining_minutes(balances)

    def _plan_flags(self, indexed: CallIndexRecord) -> tuple[bool, int]:
        subscription = self._billing.get_active_subscription(
            indexed.tenant_id, indexed.customer_id
        )
        if subscription is None:
            return False, 0
        version = self._versions.get(subscription.plan_version_id)
        if version is None:
            return False, 0
        return bool(version.overage_enabled), int(version.grace_seconds)

    def _continue_for(self, indexed: CallIndexRecord, now) -> object:
        started = indexed.created_at or now
        elapsed = max(0, int((now - started).total_seconds()))
        overage, grace = self._plan_flags(indexed)
        return decide_continue(
            remaining_minutes=self._remaining(indexed.tenant_id, indexed.customer_id),
            elapsed_seconds=elapsed,
            overage_enabled=overage,
            grace_seconds=grace,
        )

    def _drain(self, indexed: CallIndexRecord, billed: int) -> None:
        if billed <= 0:
            return
        lots = self._billing.list_lots(indexed.tenant_id, indexed.customer_id)
        balances = tuple(
            LotBalance(
                lot_id=str(lot.lot_id),
                kind=lot.kind,
                remaining_minutes=lot.remaining_minutes,
            )
            for lot in lots
        )
        try:
            drains = drain_lots(balances, billed)
        except DomainError:
            available = remaining_minutes(balances)
            if available <= 0:
                return
            drains = drain_lots(balances, available)
        by_id = {str(lot.lot_id): lot for lot in lots}
        for drain in drains:
            lot = by_id[drain.lot_id]
            self._billing.put_lot(
                indexed.tenant_id,
                MinuteLotRecord(
                    lot_id=lot.lot_id,
                    tenant_id=lot.tenant_id,
                    customer_id=lot.customer_id,
                    invoice_id=lot.invoice_id,
                    kind=LotKind(lot.kind),
                    granted_minutes=lot.granted_minutes,
                    remaining_minutes=max(0, lot.remaining_minutes - drain.minutes),
                    created_at=lot.created_at,
                ),
            )

    def _training_session(self, session_token: str):
        try:
            session_id = uuid.UUID((session_token or "").strip())
        except (ValueError, TypeError, AttributeError):
            return None, None
        mapped = self._training_index.get(session_id)
        if mapped is None:
            return None, None
        tenant_id, agent_id = mapped
        return (
            self._agents.get_session(tenant_id, session_id),
            self._agents.get_agent(tenant_id, agent_id),
        )

    def _mark_in_progress(self, indexed: CallIndexRecord) -> CallIndexRecord:
        updated = self._index.save(replace(indexed, status=CallStatus.IN_PROGRESS))
        call = self._calls.get_call(indexed.tenant_id, indexed.call_id)
        if call is not None:
            self._calls.put_call(
                indexed.tenant_id, replace(call, status=CallStatus.IN_PROGRESS)
            )
        return updated

    def _originated_payload(self, indexed: CallIndexRecord) -> dict[str, object]:
        return {
            "ok": True,
            "admitted": True,
            "vokit_call_id": str(indexed.call_id),
            "edge_call_id": indexed.edge_call_id,
            "direction": indexed.direction.value,
            "status": indexed.status.value,
            "from": indexed.e164,
            "to": indexed.remote_e164,
        }

    def _pick_destination(self, indexed: CallIndexRecord, destination_id: str):
        agent = self._agents.get_agent(indexed.tenant_id, indexed.agent_id)
        chosen = None
        raw = (destination_id or "").strip()
        if raw:
            try:
                chosen = uuid.UUID(raw)
            except (ValueError, TypeError, AttributeError):
                chosen = None
        if chosen is None and agent is not None:
            chosen = agent.default_transfer_id
        if chosen is not None:
            row = self._media.get_destination(indexed.tenant_id, chosen)
            if row is not None:
                return row
        if agent is None:
            return None
        for row in self._media.list_destinations(
            indexed.tenant_id, customer_id=agent.customer_id
        ):
            if row.status is DestinationStatus.ACTIVE:
                return row
        return None

    def _transfer_spec(self, indexed: CallIndexRecord, agent) -> dict[str, object]:
        destination = self._pick_destination(indexed, "")
        if destination is None:
            return {"configured": False}
        override = self._dest_index.get(destination.destination_id)
        if destination.status is DestinationStatus.DISABLED or (
            override is not None and override.platform_disabled
        ):
            return {"configured": False, "reason": "disabled"}
        return {
            "configured": True,
            "kind": destination.kind.value,
            "destination_id": str(destination.destination_id),
            "no_answer_seconds": destination.no_answer_seconds,
        }

    def _voicemail_spec(self, indexed: CallIndexRecord, agent) -> dict[str, object]:
        hours = parse_hours(list(agent.business_hours))
        open_now = is_within_hours(
            self._clock.now(), timezone_name=agent.timezone, windows=hours
        )
        action = after_hours_action(
            open_now=open_now, fallback_behavior=agent.fallback_behavior
        )
        inbound_required = (
            indexed.direction is CallDirection.INBOUND
            and action is AfterHoursAction.VOICEMAIL
        )
        return {
            "required": inbound_required,
            "greeting": agent.voicemail_greeting or agent.greeting,
            "outbound_message": agent.outbound_voicemail_message,
        }
