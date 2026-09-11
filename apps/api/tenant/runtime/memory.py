from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from control_plane.billing.domain.types import SubscriptionStatus
from control_plane.customers.domain.types import CustomerStatus
from control_plane.telephony.domain.types import AssignmentStatus
from control_plane.tenancy.domain.policies import (
    db_unavailable,
    isolation_violation,
    pool_exhausted,
)
from shared_kernel.errors import DomainError
from shared_kernel.time import utc_now
from tenant.agents.domain import (
    AgentVersionRecord,
    InstructionLayerRecord,
    KnowledgeAttachmentRecord,
    KnowledgeSourceRecord,
    TenantAgent,
    TestSessionRecord,
)
from tenant.billing.domain import (
    InvoiceRecord,
    MinuteLotRecord,
    PaymentRecord,
    SubscriptionRecord,
)
from tenant.calls.domain import TenantCallEventRecord, TenantCallRecord
from tenant.integrations.domain import (
    TenantConnectionRecord,
    TenantIntegrationSettings,
    TenantWebhookDelivery,
    TenantWebhookEndpoint,
)
from tenant.lifecycle.domain import AgencyProfile, TenantCustomer
from tenant.media.domain import TransferDestinationRecord, VoicemailMessageRecord
from tenant.numbers.domain import NumberAssignmentRecord
from tenant.recordings.domain import TenantArtifactRecord
from tenant.runtime.domain import IsolationRecord
from tenant.runtime.ports import ConnectionTarget, TenantConnection
from tenant.schema import CURRENT_VERSION, VERSION_ORDER


@dataclass
class MemoryConnection:
    tenant_id: uuid.UUID
    database_id: uuid.UUID
    name: str
    store: dict[uuid.UUID, IsolationRecord]
    versions: set[str]
    backend: MemoryStore
    down: bool = False

    def ping(self) -> None:
        if self.down:
            raise db_unavailable()


@dataclass
class MemoryStore:
    records: dict[uuid.UUID, IsolationRecord] = field(default_factory=dict)
    versions: set[str] = field(default_factory=set)
    down: bool = False
    created: bool = False
    agency: AgencyProfile | None = None
    customers: dict[uuid.UUID, TenantCustomer] = field(default_factory=dict)
    subscriptions: dict[uuid.UUID, SubscriptionRecord] = field(default_factory=dict)
    invoices: dict[uuid.UUID, InvoiceRecord] = field(default_factory=dict)
    payments: dict[uuid.UUID, PaymentRecord] = field(default_factory=dict)
    lots: dict[uuid.UUID, MinuteLotRecord] = field(default_factory=dict)
    agents: dict[uuid.UUID, TenantAgent] = field(default_factory=dict)
    agent_versions: dict[uuid.UUID, AgentVersionRecord] = field(default_factory=dict)
    instructions: dict[tuple[str, uuid.UUID], InstructionLayerRecord] = field(
        default_factory=dict
    )
    knowledge: dict[uuid.UUID, KnowledgeSourceRecord] = field(default_factory=dict)
    attachments: dict[tuple[uuid.UUID, uuid.UUID], KnowledgeAttachmentRecord] = field(
        default_factory=dict
    )
    sessions: dict[uuid.UUID, TestSessionRecord] = field(default_factory=dict)
    assignments: dict[uuid.UUID, NumberAssignmentRecord] = field(default_factory=dict)
    calls: dict[uuid.UUID, TenantCallRecord] = field(default_factory=dict)
    call_events: dict[uuid.UUID, TenantCallEventRecord] = field(default_factory=dict)
    destinations: dict[uuid.UUID, TransferDestinationRecord] = field(default_factory=dict)
    voicemails: dict[uuid.UUID, VoicemailMessageRecord] = field(default_factory=dict)
    artifacts: dict[uuid.UUID, TenantArtifactRecord] = field(default_factory=dict)
    connections: dict[uuid.UUID, TenantConnectionRecord] = field(default_factory=dict)
    integration_settings: dict[uuid.UUID, TenantIntegrationSettings] = field(
        default_factory=dict
    )
    webhook_endpoints: dict[uuid.UUID, TenantWebhookEndpoint] = field(default_factory=dict)
    webhook_deliveries: dict[uuid.UUID, TenantWebhookDelivery] = field(
        default_factory=dict
    )


class MemoryRuntime:
    """In-process tenant DBs. Used by isolation tests; not a production backend."""

    def __init__(self, *, max_per_tenant: int = 4, max_tenants: int = 16) -> None:
        self._stores: dict[str, MemoryStore] = {}
        self._checked_out: dict[int, MemoryConnection] = {}
        self._counts: dict[uuid.UUID, int] = {}
        self._max_per_tenant = max_per_tenant
        self._max_tenants = max_tenants

    def ensure_database(self, target: ConnectionTarget) -> None:
        store = self._stores.setdefault(target.name, MemoryStore())
        store.created = True

    def ensure_user(self, target: ConnectionTarget) -> None:
        return

    def mark_down(self, name: str, down: bool = True) -> None:
        self._stores.setdefault(name, MemoryStore()).down = down

    def open(self, target: ConnectionTarget) -> TenantConnection:
        store = self._stores.setdefault(target.name, MemoryStore())
        if store.down:
            raise db_unavailable()
        active_tenants = {tid for tid, count in self._counts.items() if count > 0}
        if target.tenant_id not in active_tenants and len(active_tenants) >= self._max_tenants:
            raise pool_exhausted()
        if self._counts.get(target.tenant_id, 0) >= self._max_per_tenant:
            raise pool_exhausted()
        connection = MemoryConnection(
            tenant_id=target.tenant_id,
            database_id=target.database_id,
            name=target.name,
            store=store.records,
            versions=store.versions,
            backend=store,
            down=store.down,
        )
        self._checked_out[id(connection)] = connection
        self._counts[target.tenant_id] = self._counts.get(target.tenant_id, 0) + 1
        return connection

    def close(self, connection: TenantConnection) -> None:
        memory = self._as_memory(connection)
        self._checked_out.pop(id(memory), None)
        current = self._counts.get(memory.tenant_id, 0)
        self._counts[memory.tenant_id] = max(0, current - 1)

    def acquire(self, target: ConnectionTarget) -> TenantConnection:
        return self.open(target)

    def release(self, connection: TenantConnection) -> None:
        self.close(connection)

    def discard(self, tenant_id: uuid.UUID) -> None:
        self._counts[tenant_id] = 0
        stale = [key for key, conn in self._checked_out.items() if conn.tenant_id == tenant_id]
        for key in stale:
            self._checked_out.pop(key, None)

    def checked_out_tenant_ids(self) -> set[uuid.UUID]:
        return {conn.tenant_id for conn in self._checked_out.values()}

    def current_version(self, connection: TenantConnection) -> str:
        memory = self._as_memory(connection)
        applied = [version for version in VERSION_ORDER if version in memory.versions]
        return applied[-1] if applied else ""

    def apply(self, connection: TenantConnection, target_version: str) -> str:
        memory = self._as_memory(connection)
        for version in VERSION_ORDER:
            memory.versions.add(version)
            if version == target_version:
                break
        return self.current_version(memory)

    def verify(self, connection: TenantConnection, expected_version: str) -> None:
        current = self.current_version(connection)
        if current != expected_version:
            raise DomainError("tenant_schema_mismatch", "Tenant schema is not verified.")

    def upsert(self, connection: TenantConnection, record: IsolationRecord) -> None:
        memory = self._as_memory(connection)
        if record.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.store[record.object_id] = IsolationRecord(
            object_id=record.object_id,
            tenant_id=memory.tenant_id,
            payload=record.payload,
            created_at=record.created_at or utc_now(),
        )

    def get(self, connection: TenantConnection, object_id: uuid.UUID) -> IsolationRecord | None:
        memory = self._as_memory(connection)
        record = memory.store.get(object_id)
        if record is None:
            return None
        if record.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return record

    def export_snapshot(self, connection: TenantConnection) -> dict[str, object]:
        memory = self._as_memory(connection)
        records = []
        for record in memory.backend.records.values():
            if record.tenant_id != memory.tenant_id:
                raise isolation_violation()
            records.append(
                {
                    "object_id": str(record.object_id),
                    "tenant_id": str(record.tenant_id),
                    "payload": record.payload,
                }
            )
        customers = []
        for customer in memory.backend.customers.values():
            if customer.tenant_id != memory.tenant_id:
                raise isolation_violation()
            customers.append(
                {
                    "customer_id": str(customer.customer_id),
                    "tenant_id": str(customer.tenant_id),
                    "display_name": customer.display_name,
                    "status": customer.status.value,
                }
            )
        return {
            "tenant_id": str(memory.tenant_id),
            "database_id": str(memory.database_id),
            "records": records,
            "customers": customers,
            "schema_versions": sorted(memory.backend.versions),
        }

    def restore_snapshot(self, connection: TenantConnection, snapshot: dict[str, object]) -> None:
        memory = self._as_memory(connection)
        if str(snapshot.get("tenant_id")) != str(memory.tenant_id):
            raise isolation_violation()
        records: dict[uuid.UUID, IsolationRecord] = {}
        for raw in snapshot.get("records") or []:
            row = raw if isinstance(raw, dict) else {}
            tenant_id = uuid.UUID(str(row["tenant_id"]))
            if tenant_id != memory.tenant_id:
                raise isolation_violation()
            object_id = uuid.UUID(str(row["object_id"]))
            records[object_id] = IsolationRecord(
                object_id=object_id,
                tenant_id=memory.tenant_id,
                payload=str(row.get("payload") or ""),
            )
        customers: dict[uuid.UUID, TenantCustomer] = {}
        for raw in snapshot.get("customers") or []:
            row = raw if isinstance(raw, dict) else {}
            tenant_id = uuid.UUID(str(row["tenant_id"]))
            if tenant_id != memory.tenant_id:
                raise isolation_violation()
            customer_id = uuid.UUID(str(row["customer_id"]))
            customers[customer_id] = TenantCustomer(
                customer_id=customer_id,
                tenant_id=memory.tenant_id,
                display_name=str(row.get("display_name") or ""),
                status=CustomerStatus(str(row.get("status") or "active")),
            )
        memory.backend.records = records
        memory.backend.customers = customers
        memory.store = memory.backend.records

    def put_agency(self, connection: TenantConnection, profile: AgencyProfile) -> None:
        memory = self._as_memory(connection)
        if profile.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.agency = profile

    def get_agency(self, connection: TenantConnection) -> AgencyProfile | None:
        memory = self._as_memory(connection)
        profile = memory.backend.agency
        if profile is None:
            return None
        if profile.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return profile

    def put_customer(self, connection: TenantConnection, customer: TenantCustomer) -> None:
        memory = self._as_memory(connection)
        if customer.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.customers[customer.customer_id] = customer

    def get_customer(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> TenantCustomer | None:
        memory = self._as_memory(connection)
        customer = memory.backend.customers.get(customer_id)
        if customer is None:
            return None
        if customer.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return customer

    def list_customers(self, connection: TenantConnection) -> list[TenantCustomer]:
        memory = self._as_memory(connection)
        rows = []
        for customer in memory.backend.customers.values():
            if customer.tenant_id != memory.tenant_id:
                raise isolation_violation()
            rows.append(customer)
        return rows

    def put_subscription(
        self, connection: TenantConnection, subscription: SubscriptionRecord
    ) -> None:
        memory = self._as_memory(connection)
        if subscription.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.subscriptions[subscription.subscription_id] = subscription

    def get_subscription(
        self, connection: TenantConnection, subscription_id: uuid.UUID
    ) -> SubscriptionRecord | None:
        memory = self._as_memory(connection)
        row = memory.backend.subscriptions.get(subscription_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def get_active_subscription(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> SubscriptionRecord | None:
        memory = self._as_memory(connection)
        for row in memory.backend.subscriptions.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if row.customer_id == customer_id and row.status is SubscriptionStatus.ACTIVE:
                return row
        return None

    def put_invoice(self, connection: TenantConnection, invoice: InvoiceRecord) -> None:
        memory = self._as_memory(connection)
        if invoice.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.invoices[invoice.invoice_id] = invoice

    def get_invoice(
        self, connection: TenantConnection, invoice_id: uuid.UUID
    ) -> InvoiceRecord | None:
        memory = self._as_memory(connection)
        row = memory.backend.invoices.get(invoice_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def list_invoices(
        self, connection: TenantConnection, customer_id: uuid.UUID | None = None
    ) -> list[InvoiceRecord]:
        memory = self._as_memory(connection)
        rows = []
        for row in memory.backend.invoices.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if customer_id is None or row.customer_id == customer_id:
                rows.append(row)
        return rows

    def put_payment(self, connection: TenantConnection, payment: PaymentRecord) -> None:
        memory = self._as_memory(connection)
        if payment.tenant_id != memory.tenant_id:
            raise isolation_violation()
        for existing in memory.backend.payments.values():
            if existing.tenant_id != memory.tenant_id:
                raise isolation_violation()
            same_event = (
                existing.processor == payment.processor
                and existing.processor_event_id == payment.processor_event_id
            )
            if same_event and existing.payment_id != payment.payment_id:
                raise DomainError(
                    "processor_event_duplicate",
                    "Payment event was already received.",
                )
        memory.backend.payments[payment.payment_id] = payment

    def list_payments(
        self, connection: TenantConnection, invoice_id: uuid.UUID | None = None
    ) -> list[PaymentRecord]:
        memory = self._as_memory(connection)
        rows = []
        for row in memory.backend.payments.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if invoice_id is None or row.invoice_id == invoice_id:
                rows.append(row)
        return rows

    def put_lot(self, connection: TenantConnection, lot: MinuteLotRecord) -> None:
        memory = self._as_memory(connection)
        if lot.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.lots[lot.lot_id] = lot

    def list_lots(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> list[MinuteLotRecord]:
        memory = self._as_memory(connection)
        rows = []
        for row in memory.backend.lots.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if row.customer_id == customer_id:
                rows.append(row)
        return rows

    def put_agent(self, connection: TenantConnection, agent: TenantAgent) -> None:
        memory = self._as_memory(connection)
        if agent.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.agents[agent.agent_id] = agent

    def get_agent(
        self, connection: TenantConnection, agent_id: uuid.UUID
    ) -> TenantAgent | None:
        memory = self._as_memory(connection)
        row = memory.backend.agents.get(agent_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def list_agents(
        self,
        connection: TenantConnection,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantAgent]:
        memory = self._as_memory(connection)
        rows = []
        for row in memory.backend.agents.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if customer_id is None or row.customer_id == customer_id:
                rows.append(row)
        return rows

    def put_version(self, connection: TenantConnection, row: AgentVersionRecord) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.agent_versions[row.version_id] = row

    def list_versions(
        self, connection: TenantConnection, agent_id: uuid.UUID
    ) -> list[AgentVersionRecord]:
        memory = self._as_memory(connection)
        rows = []
        for row in memory.backend.agent_versions.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if row.agent_id == agent_id:
                rows.append(row)
        return sorted(rows, key=lambda item: item.version)

    def put_instruction(
        self, connection: TenantConnection, row: InstructionLayerRecord
    ) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.instructions[(row.scope, row.owner_id)] = row

    def get_instruction(
        self, connection: TenantConnection, scope: str, owner_id: uuid.UUID
    ) -> InstructionLayerRecord | None:
        memory = self._as_memory(connection)
        row = memory.backend.instructions.get((scope, owner_id))
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def put_knowledge(self, connection: TenantConnection, row: KnowledgeSourceRecord) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.knowledge[row.source_id] = row

    def get_knowledge(
        self, connection: TenantConnection, source_id: uuid.UUID
    ) -> KnowledgeSourceRecord | None:
        memory = self._as_memory(connection)
        row = memory.backend.knowledge.get(source_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def list_knowledge(
        self, connection: TenantConnection, *, scope: str | None = None
    ) -> list[KnowledgeSourceRecord]:
        memory = self._as_memory(connection)
        rows = []
        for row in memory.backend.knowledge.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if scope is None or row.scope == scope:
                rows.append(row)
        return rows

    def put_attachment(
        self, connection: TenantConnection, row: KnowledgeAttachmentRecord
    ) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.attachments[(row.agent_id, row.source_id)] = row

    def list_attachments(
        self, connection: TenantConnection, agent_id: uuid.UUID
    ) -> list[KnowledgeAttachmentRecord]:
        memory = self._as_memory(connection)
        rows = []
        for row in memory.backend.attachments.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if row.agent_id == agent_id:
                rows.append(row)
        return rows

    def delete_attachment(
        self, connection: TenantConnection, agent_id: uuid.UUID, source_id: uuid.UUID
    ) -> None:
        memory = self._as_memory(connection)
        row = memory.backend.attachments.get((agent_id, source_id))
        if row is not None and row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.attachments.pop((agent_id, source_id), None)

    def put_session(self, connection: TenantConnection, row: TestSessionRecord) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.sessions[row.session_id] = row

    def put_assignment(
        self, connection: TenantConnection, row: NumberAssignmentRecord
    ) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.assignments[row.assignment_id] = row

    def get_assignment(
        self, connection: TenantConnection, assignment_id: uuid.UUID
    ) -> NumberAssignmentRecord | None:
        memory = self._as_memory(connection)
        row = memory.backend.assignments.get(assignment_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def active_for_number(
        self, connection: TenantConnection, phone_number_id: uuid.UUID
    ) -> NumberAssignmentRecord | None:
        memory = self._as_memory(connection)
        for row in memory.backend.assignments.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if (
                row.phone_number_id == phone_number_id
                and row.status is AssignmentStatus.ASSIGNED
            ):
                return row
        return None

    def list_assignments(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
    ) -> list[NumberAssignmentRecord]:
        memory = self._as_memory(connection)
        rows = []
        for row in memory.backend.assignments.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if customer_id is not None and row.customer_id != customer_id:
                continue
            if agent_id is not None and row.agent_id != agent_id:
                continue
            rows.append(row)
        return rows

    def put_call(self, connection: TenantConnection, row: TenantCallRecord) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.calls[row.call_id] = row

    def get_call(
        self, connection: TenantConnection, call_id: uuid.UUID
    ) -> TenantCallRecord | None:
        memory = self._as_memory(connection)
        row = memory.backend.calls.get(call_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def get_call_by_edge(
        self, connection: TenantConnection, edge_call_id: str
    ) -> TenantCallRecord | None:
        memory = self._as_memory(connection)
        for row in memory.backend.calls.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if row.edge_call_id == edge_call_id:
                return row
        return None

    def put_call_event(
        self, connection: TenantConnection, row: TenantCallEventRecord
    ) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.call_events[row.event_id] = row

    def list_calls(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
    ) -> list[TenantCallRecord]:
        memory = self._as_memory(connection)
        rows: list[TenantCallRecord] = []
        for row in memory.backend.calls.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if customer_id is not None and row.customer_id != customer_id:
                continue
            if agent_id is not None and row.agent_id != agent_id:
                continue
            rows.append(row)
        return sorted(rows, key=lambda item: item.started_at, reverse=True)

    def put_destination(
        self, connection: TenantConnection, row: TransferDestinationRecord
    ) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.destinations[row.destination_id] = row

    def get_destination(
        self, connection: TenantConnection, destination_id: uuid.UUID
    ) -> TransferDestinationRecord | None:
        memory = self._as_memory(connection)
        row = memory.backend.destinations.get(destination_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def list_destinations(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
    ) -> list[TransferDestinationRecord]:
        memory = self._as_memory(connection)
        rows: list[TransferDestinationRecord] = []
        for row in memory.backend.destinations.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if customer_id is not None and row.customer_id != customer_id:
                continue
            rows.append(row)
        return rows

    def put_voicemail(
        self, connection: TenantConnection, row: VoicemailMessageRecord
    ) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.voicemails[row.message_id] = row

    def get_voicemail(
        self, connection: TenantConnection, message_id: uuid.UUID
    ) -> VoicemailMessageRecord | None:
        memory = self._as_memory(connection)
        row = memory.backend.voicemails.get(message_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def list_voicemail(
        self,
        connection: TenantConnection,
        *,
        call_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[VoicemailMessageRecord]:
        memory = self._as_memory(connection)
        rows: list[VoicemailMessageRecord] = []
        for row in memory.backend.voicemails.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if call_id is not None and row.call_id != call_id:
                continue
            if customer_id is not None and row.customer_id != customer_id:
                continue
            rows.append(row)
        return rows

    def get_session(
        self, connection: TenantConnection, session_id: uuid.UUID
    ) -> TestSessionRecord | None:
        memory = self._as_memory(connection)
        row = memory.backend.sessions.get(session_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def put_artifact(
        self, connection: TenantConnection, row: TenantArtifactRecord
    ) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.artifacts[row.artifact_id] = row

    def get_artifact(
        self, connection: TenantConnection, artifact_id: uuid.UUID
    ) -> TenantArtifactRecord | None:
        memory = self._as_memory(connection)
        row = memory.backend.artifacts.get(artifact_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def list_artifacts(
        self,
        connection: TenantConnection,
        *,
        call_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantArtifactRecord]:
        memory = self._as_memory(connection)
        rows: list[TenantArtifactRecord] = []
        for row in memory.backend.artifacts.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if call_id is not None and row.call_id != call_id:
                continue
            if customer_id is not None and row.customer_id != customer_id:
                continue
            rows.append(row)
        return rows

    def put_connection(
        self, connection: TenantConnection, row: TenantConnectionRecord
    ) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.connections[row.connection_id] = row

    def get_connection(
        self, connection: TenantConnection, connection_id: uuid.UUID
    ) -> TenantConnectionRecord | None:
        memory = self._as_memory(connection)
        row = memory.backend.connections.get(connection_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def list_connections(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantConnectionRecord]:
        memory = self._as_memory(connection)
        rows: list[TenantConnectionRecord] = []
        for row in memory.backend.connections.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if customer_id is not None and row.customer_id != customer_id:
                continue
            rows.append(row)
        return rows

    def put_settings(
        self, connection: TenantConnection, row: TenantIntegrationSettings
    ) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.integration_settings[row.customer_id] = row

    def get_settings(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> TenantIntegrationSettings | None:
        memory = self._as_memory(connection)
        row = memory.backend.integration_settings.get(customer_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def put_endpoint(
        self, connection: TenantConnection, row: TenantWebhookEndpoint
    ) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.webhook_endpoints[row.endpoint_id] = row

    def get_endpoint(
        self, connection: TenantConnection, endpoint_id: uuid.UUID
    ) -> TenantWebhookEndpoint | None:
        memory = self._as_memory(connection)
        row = memory.backend.webhook_endpoints.get(endpoint_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def list_endpoints(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantWebhookEndpoint]:
        memory = self._as_memory(connection)
        rows: list[TenantWebhookEndpoint] = []
        for row in memory.backend.webhook_endpoints.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if customer_id is not None and row.customer_id != customer_id:
                continue
            rows.append(row)
        return rows

    def put_delivery(
        self, connection: TenantConnection, row: TenantWebhookDelivery
    ) -> None:
        memory = self._as_memory(connection)
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        memory.backend.webhook_deliveries[row.delivery_id] = row

    def get_delivery(
        self, connection: TenantConnection, delivery_id: uuid.UUID
    ) -> TenantWebhookDelivery | None:
        memory = self._as_memory(connection)
        row = memory.backend.webhook_deliveries.get(delivery_id)
        if row is None:
            return None
        if row.tenant_id != memory.tenant_id:
            raise isolation_violation()
        return row

    def list_deliveries(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
        endpoint_id: uuid.UUID | None = None,
    ) -> list[TenantWebhookDelivery]:
        memory = self._as_memory(connection)
        rows: list[TenantWebhookDelivery] = []
        for row in memory.backend.webhook_deliveries.values():
            if row.tenant_id != memory.tenant_id:
                raise isolation_violation()
            if customer_id is not None and row.customer_id != customer_id:
                continue
            if endpoint_id is not None and row.endpoint_id != endpoint_id:
                continue
            rows.append(row)
        return rows

    def _as_memory(self, connection: TenantConnection) -> MemoryConnection:
        if not isinstance(connection, MemoryConnection):
            raise isolation_violation()
        if connection.down:
            raise db_unavailable()
        return connection


def bootstrap_memory_schema(runtime: MemoryRuntime, target: ConnectionTarget) -> str:
    runtime.ensure_database(target)
    connection = runtime.open(target)
    try:
        runtime.apply(connection, CURRENT_VERSION)
        runtime.verify(connection, CURRENT_VERSION)
        return CURRENT_VERSION
    finally:
        runtime.close(connection)
