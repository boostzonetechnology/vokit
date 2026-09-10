from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from queue import Empty, Queue

import pymysql
from pymysql.connections import Connection

from control_plane.billing.domain.types import (
    InvoiceStatus,
    LineKind,
    LotKind,
    PaymentStatus,
    SubscriptionStatus,
)
from control_plane.customers.domain.types import CustomerStatus
from control_plane.integrations.domain.types import (
    ConnectionStatus,
    DeliveryStatus,
    EndpointStatus,
    ProviderKind,
)
from control_plane.recordings.domain.types import ArtifactKind, ArtifactStatus
from control_plane.risk.domain.types import AgentStatus
from control_plane.telephony.domain.call_types import CallDirection, CallStatus
from control_plane.telephony.domain.destinations import DestinationKind, DestinationStatus
from control_plane.telephony.domain.types import AssignmentStatus
from control_plane.telephony.domain.voicemail import VoicemailDirection, VoicemailStatus
from control_plane.tenancy.domain.lifecycle import AgencyCapabilities, AgencyStatus
from control_plane.tenancy.domain.policies import isolation_violation, pool_exhausted
from shared_kernel.errors import DomainError
from shared_kernel.secrets import SecretRef
from shared_kernel.time import utc_now
from tenant.agents.domain import (
    AgentVersionRecord,
    InstructionLayerRecord,
    KnowledgeAttachmentRecord,
    KnowledgeSourceRecord,
    TenantAgent,
    TestSessionRecord,
    agent_config_json,
    agent_from_config,
)
from tenant.billing.domain import (
    InvoiceLineRecord,
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
from tenant.media.domain import (
    TransferDestinationRecord,
    TransferMemberRecord,
    VoicemailMessageRecord,
)
from tenant.numbers.domain import NumberAssignmentRecord
from tenant.recordings.domain import TenantArtifactRecord
from tenant.runtime.domain import IsolationRecord
from tenant.runtime.ports import ConnectionTarget, TenantConnection
from tenant.schema import CURRENT_VERSION, SCHEMA_STATEMENTS, VERSION_ORDER


@dataclass
class MysqlConnection:
    tenant_id: uuid.UUID
    database_id: uuid.UUID
    raw: Connection


    def ping(self) -> None:
        self.raw.ping(reconnect=False)


@dataclass
class _PoolBucket:
    idle: Queue = field(default_factory=Queue)
    size: int = 0


class MysqlRuntime:
    def __init__(
        self,
        *,
        user: str,
        connect_timeout: int = 5,
        max_per_tenant: int = 4,
        max_tenants: int = 16,
        admin_user: str | None = None,
    ) -> None:
        self._user = user
        self._admin_user = admin_user or user
        self._connect_timeout = connect_timeout
        self._max_per_tenant = max_per_tenant
        self._max_tenants = max_tenants
        self._buckets: dict[uuid.UUID, _PoolBucket] = {}
        self._checked_out: dict[int, MysqlConnection] = {}

    def ensure_database(self, target: ConnectionTarget) -> None:
        password = SecretRef(target.secret_ref).resolve()
        try:
            existing = pymysql.connect(
                host=target.host,
                port=target.port,
                user=self._user,
                password=password,
                database=target.name,
                connect_timeout=self._connect_timeout,
                charset="utf8mb4",
                ssl=self._ssl(target),
                autocommit=True,
            )
            existing.close()
            return
        except pymysql.err.OperationalError:
            pass
        raw = pymysql.connect(
            host=target.host,
            port=target.port,
            user=self._admin_user,
            password=password,
            connect_timeout=self._connect_timeout,
            charset="utf8mb4",
            ssl=self._ssl(target),
            autocommit=True,
        )
        try:
            with raw.cursor() as cursor:
                ident = _safe_ident(target.name)
                ddl = (
                    f"CREATE DATABASE IF NOT EXISTS `{ident}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                cursor.execute(ddl)
        finally:
            raw.close()

    def open(self, target: ConnectionTarget) -> TenantConnection:
        password = SecretRef(target.secret_ref).resolve()
        raw = pymysql.connect(
            host=target.host,
            port=target.port,
            user=self._user,
            password=password,
            database=target.name,
            connect_timeout=self._connect_timeout,
            charset="utf8mb4",
            ssl=self._ssl(target),
            autocommit=True,
        )
        connection = MysqlConnection(
            tenant_id=target.tenant_id,
            database_id=target.database_id,
            raw=raw,
        )
        self._checked_out[id(connection)] = connection
        return connection

    def close(self, connection: TenantConnection) -> None:
        mysql = self._as_mysql(connection)
        self._checked_out.pop(id(mysql), None)
        mysql.raw.close()

    def acquire(self, target: ConnectionTarget) -> TenantConnection:
        bucket = self._buckets.setdefault(target.tenant_id, _PoolBucket())
        active_tenants = {tid for tid, item in self._buckets.items() if item.size > 0}
        if target.tenant_id not in active_tenants and len(active_tenants) >= self._max_tenants:
            raise pool_exhausted()
        try:
            connection = bucket.idle.get_nowait()
            if connection.tenant_id != target.tenant_id:
                self.close(connection)
                raise isolation_violation()
            connection.ping()
            self._checked_out[id(connection)] = connection
            return connection
        except Empty:
            if bucket.size >= self._max_per_tenant:
                raise pool_exhausted() from None
            connection = self.open(target)
            bucket.size += 1
            return connection

    def release(self, connection: TenantConnection) -> None:
        mysql = self._as_mysql(connection)
        self._checked_out.pop(id(mysql), None)
        bucket = self._buckets.setdefault(mysql.tenant_id, _PoolBucket())
        bucket.idle.put(mysql)

    def discard(self, tenant_id: uuid.UUID) -> None:
        bucket = self._buckets.pop(tenant_id, None)
        if bucket is None:
            return
        while True:
            try:
                connection = bucket.idle.get_nowait()
            except Empty:
                break
            connection.raw.close()
        stale = [key for key, conn in self._checked_out.items() if conn.tenant_id == tenant_id]
        for key in stale:
            conn = self._checked_out.pop(key)
            conn.raw.close()

    def checked_out_tenant_ids(self) -> set[uuid.UUID]:
        return {conn.tenant_id for conn in self._checked_out.values()}

    def current_version(self, connection: TenantConnection) -> str:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                "SELECT version FROM tenant_schema_migrations "
                "ORDER BY applied_at DESC, version DESC LIMIT 1"
            )
            row = cursor.fetchone()
        return str(row[0]) if row else ""

    def apply(self, connection: TenantConnection, target_version: str) -> str:
        mysql = self._as_mysql(connection)
        applied = set(self._applied_versions(mysql))
        for version in VERSION_ORDER:
            if version in applied:
                if version == target_version:
                    break
                continue
            for statement in SCHEMA_STATEMENTS[version]:
                with mysql.raw.cursor() as cursor:
                    cursor.execute(statement)
            with mysql.raw.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO tenant_schema_migrations (version, applied_at) VALUES (%s, %s)",
                    (version, utc_now()),
                )
            if version == target_version:
                break
        return self.current_version(mysql)

    def verify(self, connection: TenantConnection, expected_version: str) -> None:
        current = self.current_version(connection)
        if current != expected_version:
            raise DomainError("tenant_schema_mismatch", "Tenant schema is not verified.")
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute("SELECT 1 FROM tenant_isolation_records LIMIT 1")

    def export_snapshot(self, connection: TenantConnection) -> dict[str, object]:
        raise DomainError(
            "backup_use_logical_dump",
            "MySQL tenant restore uses per-database mysqldump, not an in-process snapshot.",
            http_status=501,
        )

    def restore_snapshot(
        self, connection: TenantConnection, snapshot: dict[str, object]
    ) -> None:
        raise DomainError(
            "backup_use_logical_dump",
            "MySQL tenant restore uses per-database mysql client, not an in-process snapshot.",
            http_status=501,
        )

    def upsert(self, connection: TenantConnection, record: IsolationRecord) -> None:
        mysql = self._as_mysql(connection)
        if record.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tenant_isolation_records (object_id, tenant_id, payload, created_at)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE payload = VALUES(payload)
                """,
                (
                    str(record.object_id),
                    str(mysql.tenant_id),
                    record.payload,
                    record.created_at or utc_now(),
                ),
            )

    def get(self, connection: TenantConnection, object_id: uuid.UUID) -> IsolationRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT object_id, tenant_id, payload, created_at
                FROM tenant_isolation_records
                WHERE object_id = %s
                """,
                (str(object_id),),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return IsolationRecord(
            object_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            payload=str(row[2]),
            created_at=row[3],
        )

    def put_agency(self, connection: TenantConnection, profile: AgencyProfile) -> None:
        mysql = self._as_mysql(connection)
        if profile.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        caps = profile.capabilities
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO agency_profiles (
                    tenant_id, display_name, legal_name, status, currency,
                    create_customers, create_agents, purchase_numbers,
                    request_payouts, existing_customer_services, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    display_name = VALUES(display_name),
                    legal_name = VALUES(legal_name),
                    status = VALUES(status),
                    currency = VALUES(currency),
                    create_customers = VALUES(create_customers),
                    create_agents = VALUES(create_agents),
                    purchase_numbers = VALUES(purchase_numbers),
                    request_payouts = VALUES(request_payouts),
                    existing_customer_services = VALUES(
                        existing_customer_services
                    ),
                    updated_at = VALUES(updated_at)
                """,
                (
                    str(mysql.tenant_id),
                    profile.display_name,
                    profile.legal_name,
                    profile.status.value,
                    profile.currency,
                    int(caps.create_customers),
                    int(caps.create_agents),
                    int(caps.purchase_numbers),
                    int(caps.request_payouts),
                    int(caps.existing_customer_services),
                    profile.updated_at or utc_now(),
                ),
            )

    def get_agency(self, connection: TenantConnection) -> AgencyProfile | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT tenant_id, display_name, legal_name, status, currency,
                       create_customers, create_agents, purchase_numbers,
                       request_payouts, existing_customer_services, updated_at
                FROM agency_profiles
                WHERE tenant_id = %s
                """,
                (str(mysql.tenant_id),),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        tenant_id = uuid.UUID(str(row[0]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return AgencyProfile(
            tenant_id=tenant_id,
            display_name=str(row[1]),
            legal_name=str(row[2]),
            status=AgencyStatus(str(row[3])),
            currency=str(row[4]),
            capabilities=AgencyCapabilities(
                create_customers=bool(row[5]),
                create_agents=bool(row[6]),
                purchase_numbers=bool(row[7]),
                request_payouts=bool(row[8]),
                existing_customer_services=bool(row[9]),
            ),
            updated_at=row[10],
        )

    def put_customer(self, connection: TenantConnection, customer: TenantCustomer) -> None:
        mysql = self._as_mysql(connection)
        if customer.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        now = customer.updated_at or utc_now()
        created = customer.created_at or now
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO customers (
                    customer_id, tenant_id, display_name, status,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    display_name = VALUES(display_name),
                    status = VALUES(status),
                    updated_at = VALUES(updated_at)
                """,
                (
                    str(customer.customer_id),
                    str(mysql.tenant_id),
                    customer.display_name,
                    customer.status.value,
                    created,
                    now,
                ),
            )

    def get_customer(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> TenantCustomer | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT customer_id, tenant_id, display_name, status,
                       created_at, updated_at
                FROM customers
                WHERE customer_id = %s AND tenant_id = %s
                """,
                (str(customer_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return TenantCustomer(
            customer_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            display_name=str(row[2]),
            status=CustomerStatus(str(row[3])),
            created_at=row[4],
            updated_at=row[5],
        )

    def list_customers(self, connection: TenantConnection) -> list[TenantCustomer]:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT customer_id, tenant_id, display_name, status,
                       created_at, updated_at
                FROM customers
                WHERE tenant_id = %s
                ORDER BY created_at
                """,
                (str(mysql.tenant_id),),
            )
            rows = cursor.fetchall()
        customers: list[TenantCustomer] = []
        for row in rows:
            tenant_id = uuid.UUID(str(row[1]))
            if tenant_id != mysql.tenant_id:
                raise isolation_violation()
            customers.append(
                TenantCustomer(
                    customer_id=uuid.UUID(str(row[0])),
                    tenant_id=tenant_id,
                    display_name=str(row[2]),
                    status=CustomerStatus(str(row[3])),
                    created_at=row[4],
                    updated_at=row[5],
                )
            )
        return customers

    def put_subscription(
        self, connection: TenantConnection, subscription: SubscriptionRecord
    ) -> None:
        mysql = self._as_mysql(connection)
        if subscription.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        now = subscription.updated_at or utc_now()
        created = subscription.created_at or now
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO subscriptions (
                    subscription_id, tenant_id, customer_id, plan_id, plan_version_id,
                    status, cycle, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    plan_id = VALUES(plan_id),
                    plan_version_id = VALUES(plan_version_id),
                    updated_at = VALUES(updated_at)
                """,
                (
                    str(subscription.subscription_id),
                    str(mysql.tenant_id),
                    str(subscription.customer_id),
                    str(subscription.plan_id),
                    str(subscription.plan_version_id),
                    subscription.status.value,
                    subscription.cycle,
                    created,
                    now,
                ),
            )

    def get_subscription(
        self, connection: TenantConnection, subscription_id: uuid.UUID
    ) -> SubscriptionRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT subscription_id, tenant_id, customer_id, plan_id, plan_version_id,
                       status, cycle, created_at, updated_at
                FROM subscriptions
                WHERE subscription_id = %s AND tenant_id = %s
                """,
                (str(subscription_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        return self._subscription(row, mysql.tenant_id) if row else None

    def get_active_subscription(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> SubscriptionRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT subscription_id, tenant_id, customer_id, plan_id, plan_version_id,
                       status, cycle, created_at, updated_at
                FROM subscriptions
                WHERE tenant_id = %s AND customer_id = %s AND status = %s
                ORDER BY created_at
                LIMIT 1
                """,
                (str(mysql.tenant_id), str(customer_id), SubscriptionStatus.ACTIVE.value),
            )
            row = cursor.fetchone()
        return self._subscription(row, mysql.tenant_id) if row else None

    def put_invoice(self, connection: TenantConnection, invoice: InvoiceRecord) -> None:
        mysql = self._as_mysql(connection)
        if invoice.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        now = invoice.updated_at or utc_now()
        created = invoice.created_at or now
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO invoices (
                    invoice_id, tenant_id, customer_id, subscription_id, status,
                    currency, total_minor, created_at, updated_at, paid_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    total_minor = VALUES(total_minor),
                    updated_at = VALUES(updated_at),
                    paid_at = VALUES(paid_at)
                """,
                (
                    str(invoice.invoice_id),
                    str(mysql.tenant_id),
                    str(invoice.customer_id),
                    str(invoice.subscription_id) if invoice.subscription_id else None,
                    invoice.status.value,
                    invoice.currency,
                    invoice.total_minor,
                    created,
                    now,
                    invoice.paid_at,
                ),
            )
            cursor.execute(
                "DELETE FROM invoice_lines WHERE invoice_id = %s AND tenant_id = %s",
                (str(invoice.invoice_id), str(mysql.tenant_id)),
            )
            for line in invoice.lines:
                cursor.execute(
                    """
                    INSERT INTO invoice_lines (
                        line_id, invoice_id, tenant_id, kind, description,
                        amount_minor, currency, minutes, commissionable
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(line.line_id),
                        str(invoice.invoice_id),
                        str(mysql.tenant_id),
                        line.kind.value,
                        line.description,
                        line.amount_minor,
                        line.currency,
                        line.minutes,
                        int(line.commissionable),
                    ),
                )

    def get_invoice(
        self, connection: TenantConnection, invoice_id: uuid.UUID
    ) -> InvoiceRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT invoice_id, tenant_id, customer_id, subscription_id, status,
                       currency, total_minor, created_at, updated_at, paid_at
                FROM invoices
                WHERE invoice_id = %s AND tenant_id = %s
                """,
                (str(invoice_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._invoice(row, self._invoice_lines(mysql, invoice_id), mysql.tenant_id)

    def list_invoices(
        self, connection: TenantConnection, customer_id: uuid.UUID | None = None
    ) -> list[InvoiceRecord]:
        mysql = self._as_mysql(connection)
        sql = """
            SELECT invoice_id, tenant_id, customer_id, subscription_id, status,
                   currency, total_minor, created_at, updated_at, paid_at
            FROM invoices
            WHERE tenant_id = %s
        """
        params: list[object] = [str(mysql.tenant_id)]
        if customer_id is not None:
            sql += " AND customer_id = %s"
            params.append(str(customer_id))
        sql += " ORDER BY created_at"
        with mysql.raw.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return [
            self._invoice(
                row,
                self._invoice_lines(mysql, uuid.UUID(str(row[0]))),
                mysql.tenant_id,
            )
            for row in rows
        ]

    def put_payment(self, connection: TenantConnection, payment: PaymentRecord) -> None:
        mysql = self._as_mysql(connection)
        if payment.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        try:
            with mysql.raw.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO payments (
                        payment_id, invoice_id, tenant_id, customer_id, processor,
                        processor_event_id, amount_minor, currency, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        status = VALUES(status),
                        amount_minor = VALUES(amount_minor)
                    """,
                    (
                        str(payment.payment_id),
                        str(payment.invoice_id),
                        str(mysql.tenant_id),
                        str(payment.customer_id),
                        payment.processor,
                        payment.processor_event_id,
                        payment.amount_minor,
                        payment.currency,
                        payment.status.value,
                        payment.created_at or utc_now(),
                    ),
                )
        except pymysql.err.IntegrityError as exc:
            raise DomainError(
                "processor_event_duplicate",
                "Payment event was already received.",
            ) from exc

    def list_payments(
        self, connection: TenantConnection, invoice_id: uuid.UUID | None = None
    ) -> list[PaymentRecord]:
        mysql = self._as_mysql(connection)
        sql = """
            SELECT payment_id, invoice_id, tenant_id, customer_id, processor,
                   processor_event_id, amount_minor, currency, status, created_at
            FROM payments
            WHERE tenant_id = %s
        """
        params: list[object] = [str(mysql.tenant_id)]
        if invoice_id is not None:
            sql += " AND invoice_id = %s"
            params.append(str(invoice_id))
        sql += " ORDER BY created_at"
        with mysql.raw.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        payments = []
        for row in rows:
            tenant_id = uuid.UUID(str(row[2]))
            if tenant_id != mysql.tenant_id:
                raise isolation_violation()
            payments.append(
                PaymentRecord(
                    payment_id=uuid.UUID(str(row[0])),
                    invoice_id=uuid.UUID(str(row[1])),
                    tenant_id=tenant_id,
                    customer_id=uuid.UUID(str(row[3])),
                    processor=str(row[4]),
                    processor_event_id=str(row[5]),
                    amount_minor=int(row[6]),
                    currency=str(row[7]),
                    status=PaymentStatus(str(row[8])),
                    created_at=row[9],
                )
            )
        return payments

    def put_lot(self, connection: TenantConnection, lot: MinuteLotRecord) -> None:
        mysql = self._as_mysql(connection)
        if lot.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO minute_lots (
                    lot_id, tenant_id, customer_id, invoice_id, kind,
                    granted_minutes, remaining_minutes, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    remaining_minutes = VALUES(remaining_minutes)
                """,
                (
                    str(lot.lot_id),
                    str(mysql.tenant_id),
                    str(lot.customer_id),
                    str(lot.invoice_id),
                    lot.kind.value,
                    lot.granted_minutes,
                    lot.remaining_minutes,
                    lot.created_at or utc_now(),
                ),
            )

    def list_lots(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> list[MinuteLotRecord]:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT lot_id, tenant_id, customer_id, invoice_id, kind,
                       granted_minutes, remaining_minutes, created_at
                FROM minute_lots
                WHERE tenant_id = %s AND customer_id = %s
                ORDER BY created_at
                """,
                (str(mysql.tenant_id), str(customer_id)),
            )
            rows = cursor.fetchall()
        lots = []
        for row in rows:
            tenant_id = uuid.UUID(str(row[1]))
            if tenant_id != mysql.tenant_id:
                raise isolation_violation()
            lots.append(
                MinuteLotRecord(
                    lot_id=uuid.UUID(str(row[0])),
                    tenant_id=tenant_id,
                    customer_id=uuid.UUID(str(row[2])),
                    invoice_id=uuid.UUID(str(row[3])),
                    kind=LotKind(str(row[4])),
                    granted_minutes=int(row[5]),
                    remaining_minutes=int(row[6]),
                    created_at=row[7],
                )
            )
        return lots

    def put_agent(self, connection: TenantConnection, agent: TenantAgent) -> None:
        mysql = self._as_mysql(connection)
        if agent.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        now = agent.updated_at or utc_now()
        created = agent.created_at or now
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO agents (
                    agent_id, tenant_id, customer_id, display_name, status,
                    created_at, updated_at, config_json, published_version,
                    draft_version, template_id, customer_can_edit
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    display_name = VALUES(display_name),
                    status = VALUES(status),
                    updated_at = VALUES(updated_at),
                    config_json = VALUES(config_json),
                    published_version = VALUES(published_version),
                    draft_version = VALUES(draft_version),
                    template_id = VALUES(template_id),
                    customer_can_edit = VALUES(customer_can_edit)
                """,
                (
                    str(agent.agent_id),
                    str(mysql.tenant_id),
                    str(agent.customer_id),
                    agent.display_name,
                    agent.status.value,
                    created,
                    now,
                    agent_config_json(agent),
                    agent.published_version,
                    agent.draft_version,
                    str(agent.template_id) if agent.template_id else None,
                    1 if agent.customer_can_edit else 0,
                ),
            )

    def get_agent(
        self, connection: TenantConnection, agent_id: uuid.UUID
    ) -> TenantAgent | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT agent_id, tenant_id, customer_id, display_name, status,
                       created_at, updated_at, config_json, published_version,
                       draft_version, template_id, customer_can_edit
                FROM agents
                WHERE agent_id = %s AND tenant_id = %s
                """,
                (str(agent_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._agent_row(mysql, row)

    def list_agents(
        self,
        connection: TenantConnection,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantAgent]:
        mysql = self._as_mysql(connection)
        sql = """
            SELECT agent_id, tenant_id, customer_id, display_name, status,
                   created_at, updated_at, config_json, published_version,
                   draft_version, template_id, customer_can_edit
            FROM agents
            WHERE tenant_id = %s
        """
        params: list[object] = [str(mysql.tenant_id)]
        if customer_id is not None:
            sql += " AND customer_id = %s"
            params.append(str(customer_id))
        sql += " ORDER BY created_at"
        with mysql.raw.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return [self._agent_row(mysql, row) for row in rows]

    def _agent_row(self, mysql: MysqlConnection, row) -> TenantAgent:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        template_id = uuid.UUID(str(row[10])) if row[10] else None
        return agent_from_config(
            agent_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            display_name=str(row[3]),
            status=AgentStatus(str(row[4])),
            created_at=row[5],
            updated_at=row[6],
            config_json=row[7],
            published_version=int(row[8]) if row[8] is not None else None,
            draft_version=int(row[9] or 1),
            template_id=template_id,
            customer_can_edit=bool(row[11]),
        )

    def put_version(self, connection: TenantConnection, row: AgentVersionRecord) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO agent_versions (
                    version_id, agent_id, tenant_id, version, published, snapshot, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    published = VALUES(published),
                    snapshot = VALUES(snapshot)
                """,
                (
                    str(row.version_id),
                    str(row.agent_id),
                    str(mysql.tenant_id),
                    row.version,
                    1 if row.published else 0,
                    row.snapshot,
                    row.created_at or utc_now(),
                ),
            )

    def list_versions(
        self, connection: TenantConnection, agent_id: uuid.UUID
    ) -> list[AgentVersionRecord]:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT version_id, agent_id, tenant_id, version, published, snapshot, created_at
                FROM agent_versions
                WHERE tenant_id = %s AND agent_id = %s
                ORDER BY version
                """,
                (str(mysql.tenant_id), str(agent_id)),
            )
            rows = cursor.fetchall()
        versions = []
        for row in rows:
            tenant_id = uuid.UUID(str(row[2]))
            if tenant_id != mysql.tenant_id:
                raise isolation_violation()
            versions.append(
                AgentVersionRecord(
                    version_id=uuid.UUID(str(row[0])),
                    agent_id=uuid.UUID(str(row[1])),
                    tenant_id=tenant_id,
                    version=int(row[3]),
                    published=bool(row[4]),
                    snapshot=str(row[5]),
                    created_at=row[6],
                )
            )
        return versions

    def put_instruction(
        self, connection: TenantConnection, row: InstructionLayerRecord
    ) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO instruction_layers (tenant_id, scope, owner_id, body, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE body = VALUES(body), updated_at = VALUES(updated_at)
                """,
                (
                    str(mysql.tenant_id),
                    row.scope,
                    str(row.owner_id),
                    row.body,
                    row.updated_at or utc_now(),
                ),
            )

    def get_instruction(
        self, connection: TenantConnection, scope: str, owner_id: uuid.UUID
    ) -> InstructionLayerRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT tenant_id, scope, owner_id, body, updated_at
                FROM instruction_layers
                WHERE tenant_id = %s AND scope = %s AND owner_id = %s
                """,
                (str(mysql.tenant_id), scope, str(owner_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        tenant_id = uuid.UUID(str(row[0]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return InstructionLayerRecord(
            tenant_id=tenant_id,
            scope=str(row[1]),
            owner_id=uuid.UUID(str(row[2])),
            body=str(row[3]),
            updated_at=row[4],
        )

    def put_knowledge(self, connection: TenantConnection, row: KnowledgeSourceRecord) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        now = row.updated_at or utc_now()
        created = row.created_at or now
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO knowledge_sources (
                    source_id, tenant_id, scope, owner_id, kind, title, body,
                    object_ref, checksum, status, group_id, customer_can_edit,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    body = VALUES(body),
                    object_ref = VALUES(object_ref),
                    checksum = VALUES(checksum),
                    status = VALUES(status),
                    group_id = VALUES(group_id),
                    customer_can_edit = VALUES(customer_can_edit),
                    updated_at = VALUES(updated_at)
                """,
                (
                    str(row.source_id),
                    str(mysql.tenant_id),
                    row.scope,
                    str(row.owner_id),
                    row.kind,
                    row.title,
                    row.body,
                    row.object_ref,
                    row.checksum,
                    row.status,
                    row.group_id,
                    1 if row.customer_can_edit else 0,
                    created,
                    now,
                ),
            )

    def get_knowledge(
        self, connection: TenantConnection, source_id: uuid.UUID
    ) -> KnowledgeSourceRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT source_id, tenant_id, scope, owner_id, kind, title, body,
                       object_ref, checksum, status, group_id, customer_can_edit,
                       created_at, updated_at
                FROM knowledge_sources
                WHERE source_id = %s AND tenant_id = %s
                """,
                (str(source_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._knowledge_row(mysql, row)

    def list_knowledge(
        self, connection: TenantConnection, *, scope: str | None = None
    ) -> list[KnowledgeSourceRecord]:
        mysql = self._as_mysql(connection)
        sql = """
            SELECT source_id, tenant_id, scope, owner_id, kind, title, body,
                   object_ref, checksum, status, group_id, customer_can_edit,
                   created_at, updated_at
            FROM knowledge_sources
            WHERE tenant_id = %s
        """
        params: list[object] = [str(mysql.tenant_id)]
        if scope:
            sql += " AND scope = %s"
            params.append(scope)
        with mysql.raw.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return [self._knowledge_row(mysql, row) for row in rows]

    def _knowledge_row(self, mysql: MysqlConnection, row) -> KnowledgeSourceRecord:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return KnowledgeSourceRecord(
            source_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            scope=str(row[2]),
            owner_id=uuid.UUID(str(row[3])),
            kind=str(row[4]),
            title=str(row[5]),
            body=str(row[6]),
            object_ref=str(row[7]),
            checksum=str(row[8]),
            status=str(row[9]),
            group_id=str(row[10]),
            customer_can_edit=bool(row[11]),
            created_at=row[12],
            updated_at=row[13],
        )

    def put_attachment(
        self, connection: TenantConnection, row: KnowledgeAttachmentRecord
    ) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO knowledge_attachments (
                    agent_id, source_id, tenant_id, scope, group_id
                ) VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    scope = VALUES(scope),
                    group_id = VALUES(group_id)
                """,
                (
                    str(row.agent_id),
                    str(row.source_id),
                    str(mysql.tenant_id),
                    row.scope,
                    row.group_id,
                ),
            )

    def list_attachments(
        self, connection: TenantConnection, agent_id: uuid.UUID
    ) -> list[KnowledgeAttachmentRecord]:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT agent_id, source_id, tenant_id, scope, group_id
                FROM knowledge_attachments
                WHERE tenant_id = %s AND agent_id = %s
                """,
                (str(mysql.tenant_id), str(agent_id)),
            )
            rows = cursor.fetchall()
        attachments = []
        for row in rows:
            tenant_id = uuid.UUID(str(row[2]))
            if tenant_id != mysql.tenant_id:
                raise isolation_violation()
            attachments.append(
                KnowledgeAttachmentRecord(
                    agent_id=uuid.UUID(str(row[0])),
                    source_id=uuid.UUID(str(row[1])),
                    tenant_id=tenant_id,
                    scope=str(row[3]),
                    group_id=str(row[4]),
                )
            )
        return attachments

    def delete_attachment(
        self, connection: TenantConnection, agent_id: uuid.UUID, source_id: uuid.UUID
    ) -> None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM knowledge_attachments
                WHERE tenant_id = %s AND agent_id = %s AND source_id = %s
                """,
                (str(mysql.tenant_id), str(agent_id), str(source_id)),
            )

    def put_session(self, connection: TenantConnection, row: TestSessionRecord) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO agent_test_sessions (
                    session_id, tenant_id, customer_id, agent_id, kind, status,
                    created_at, ended_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    ended_at = VALUES(ended_at)
                """,
                (
                    str(row.session_id),
                    str(mysql.tenant_id),
                    str(row.customer_id),
                    str(row.agent_id),
                    row.kind,
                    row.status,
                    row.created_at or utc_now(),
                    row.ended_at,
                ),
            )

    def get_session(
        self, connection: TenantConnection, session_id: uuid.UUID
    ) -> TestSessionRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT session_id, tenant_id, customer_id, agent_id, kind, status,
                       created_at, ended_at
                FROM agent_test_sessions
                WHERE session_id = %s AND tenant_id = %s
                """,
                (str(session_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return TestSessionRecord(
            session_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            agent_id=uuid.UUID(str(row[3])),
            kind=str(row[4]),
            status=str(row[5]),
            created_at=row[6],
            ended_at=row[7],
        )

    def _invoice_lines(self, mysql: MysqlConnection, invoice_id: uuid.UUID):
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT line_id, kind, description, amount_minor, currency,
                       minutes, commissionable
                FROM invoice_lines
                WHERE invoice_id = %s AND tenant_id = %s
                """,
                (str(invoice_id), str(mysql.tenant_id)),
            )
            rows = cursor.fetchall()
        return tuple(
            InvoiceLineRecord(
                line_id=uuid.UUID(str(row[0])),
                kind=LineKind(str(row[1])),
                description=str(row[2]),
                amount_minor=int(row[3]),
                currency=str(row[4]),
                minutes=int(row[5]),
                commissionable=bool(row[6]),
            )
            for row in rows
        )

    def _invoice(self, row, lines, expected_tenant: uuid.UUID) -> InvoiceRecord:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != expected_tenant:
            raise isolation_violation()
        subscription_id = uuid.UUID(str(row[3])) if row[3] else None
        return InvoiceRecord(
            invoice_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            subscription_id=subscription_id,
            status=InvoiceStatus(str(row[4])),
            currency=str(row[5]),
            total_minor=int(row[6]),
            lines=lines,
            created_at=row[7],
            updated_at=row[8],
            paid_at=row[9],
        )

    def _subscription(self, row, expected_tenant: uuid.UUID) -> SubscriptionRecord:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != expected_tenant:
            raise isolation_violation()
        return SubscriptionRecord(
            subscription_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            plan_id=uuid.UUID(str(row[3])),
            plan_version_id=uuid.UUID(str(row[4])),
            status=SubscriptionStatus(str(row[5])),
            cycle=str(row[6]),
            created_at=row[7],
            updated_at=row[8],
        )

    def put_assignment(
        self, connection: TenantConnection, row: NumberAssignmentRecord
    ) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO number_assignments (
                    assignment_id, tenant_id, customer_id, agent_id, phone_number_id,
                    e164, status, invoice_id, assigned_at, released_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    invoice_id = VALUES(invoice_id),
                    released_at = VALUES(released_at)
                """,
                (
                    str(row.assignment_id),
                    str(mysql.tenant_id),
                    str(row.customer_id),
                    str(row.agent_id),
                    str(row.phone_number_id),
                    row.e164,
                    row.status.value,
                    str(row.invoice_id) if row.invoice_id else None,
                    row.assigned_at,
                    row.released_at,
                ),
            )

    def get_assignment(
        self, connection: TenantConnection, assignment_id: uuid.UUID
    ) -> NumberAssignmentRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT assignment_id, tenant_id, customer_id, agent_id, phone_number_id,
                       e164, status, invoice_id, assigned_at, released_at
                FROM number_assignments
                WHERE assignment_id = %s AND tenant_id = %s
                """,
                (str(assignment_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._assignment_row(mysql, row)

    def active_for_number(
        self, connection: TenantConnection, phone_number_id: uuid.UUID
    ) -> NumberAssignmentRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT assignment_id, tenant_id, customer_id, agent_id, phone_number_id,
                       e164, status, invoice_id, assigned_at, released_at
                FROM number_assignments
                WHERE phone_number_id = %s AND tenant_id = %s AND status = %s
                """,
                (
                    str(phone_number_id),
                    str(mysql.tenant_id),
                    AssignmentStatus.ASSIGNED.value,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._assignment_row(mysql, row)

    def list_assignments(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
    ) -> list[NumberAssignmentRecord]:
        mysql = self._as_mysql(connection)
        sql = """
            SELECT assignment_id, tenant_id, customer_id, agent_id, phone_number_id,
                   e164, status, invoice_id, assigned_at, released_at
            FROM number_assignments
            WHERE tenant_id = %s
        """
        params: list[object] = [str(mysql.tenant_id)]
        if customer_id is not None:
            sql += " AND customer_id = %s"
            params.append(str(customer_id))
        if agent_id is not None:
            sql += " AND agent_id = %s"
            params.append(str(agent_id))
        sql += " ORDER BY assigned_at"
        with mysql.raw.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return [self._assignment_row(mysql, row) for row in rows]

    def _assignment_row(self, mysql: MysqlConnection, row) -> NumberAssignmentRecord:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return NumberAssignmentRecord(
            assignment_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            agent_id=uuid.UUID(str(row[3])),
            phone_number_id=uuid.UUID(str(row[4])),
            e164=str(row[5]),
            status=AssignmentStatus(str(row[6])),
            invoice_id=uuid.UUID(str(row[7])) if row[7] else None,
            assigned_at=row[8],
            released_at=row[9],
        )

    def put_call(self, connection: TenantConnection, row: TenantCallRecord) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO calls (
                    call_id, tenant_id, customer_id, agent_id, phone_number_id, e164,
                    edge_call_id, sip_call_id, direction, status, billed_minutes,
                    duration_seconds, end_reason, started_at, ended_at, remote_e164,
                    transfer_destination_id, voicemail_status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    billed_minutes = VALUES(billed_minutes),
                    duration_seconds = VALUES(duration_seconds),
                    end_reason = VALUES(end_reason),
                    ended_at = VALUES(ended_at),
                    remote_e164 = VALUES(remote_e164),
                    transfer_destination_id = VALUES(transfer_destination_id),
                    voicemail_status = VALUES(voicemail_status)
                """,
                (
                    str(row.call_id),
                    str(mysql.tenant_id),
                    str(row.customer_id),
                    str(row.agent_id),
                    str(row.phone_number_id) if row.phone_number_id else None,
                    row.e164,
                    row.edge_call_id,
                    row.sip_call_id,
                    row.direction.value,
                    row.status.value,
                    row.billed_minutes,
                    row.duration_seconds,
                    row.end_reason,
                    row.started_at,
                    row.ended_at,
                    row.remote_e164,
                    str(row.transfer_destination_id) if row.transfer_destination_id else None,
                    row.voicemail_status,
                ),
            )

    def get_call(
        self, connection: TenantConnection, call_id: uuid.UUID
    ) -> TenantCallRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT call_id, tenant_id, customer_id, agent_id, phone_number_id, e164,
                       edge_call_id, sip_call_id, direction, status, billed_minutes,
                       duration_seconds, end_reason, started_at, ended_at, remote_e164,
                       transfer_destination_id, voicemail_status
                FROM calls
                WHERE call_id = %s AND tenant_id = %s
                """,
                (str(call_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._call_row(mysql, row)

    def get_call_by_edge(
        self, connection: TenantConnection, edge_call_id: str
    ) -> TenantCallRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT call_id, tenant_id, customer_id, agent_id, phone_number_id, e164,
                       edge_call_id, sip_call_id, direction, status, billed_minutes,
                       duration_seconds, end_reason, started_at, ended_at, remote_e164,
                       transfer_destination_id, voicemail_status
                FROM calls
                WHERE edge_call_id = %s AND tenant_id = %s
                """,
                (edge_call_id, str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._call_row(mysql, row)

    def put_call_event(
        self, connection: TenantConnection, row: TenantCallEventRecord
    ) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO call_events (
                    event_id, call_id, tenant_id, event_type, role, reason, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE reason = VALUES(reason)
                """,
                (
                    str(row.event_id),
                    str(row.call_id),
                    str(mysql.tenant_id),
                    row.event_type,
                    row.role,
                    row.reason,
                    row.created_at,
                ),
            )

    def list_calls(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
    ) -> list[TenantCallRecord]:
        mysql = self._as_mysql(connection)
        clauses = ["tenant_id = %s"]
        params: list[object] = [str(mysql.tenant_id)]
        if customer_id is not None:
            clauses.append("customer_id = %s")
            params.append(str(customer_id))
        if agent_id is not None:
            clauses.append("agent_id = %s")
            params.append(str(agent_id))
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT call_id, tenant_id, customer_id, agent_id, phone_number_id, e164,
                       edge_call_id, sip_call_id, direction, status, billed_minutes,
                       duration_seconds, end_reason, started_at, ended_at, remote_e164,
                       transfer_destination_id, voicemail_status
                FROM calls
                WHERE {" AND ".join(clauses)}
                ORDER BY started_at DESC
                """,
                params,
            )
            rows = cursor.fetchall()
        return [self._call_row(mysql, row) for row in rows]

    def put_destination(
        self, connection: TenantConnection, row: TransferDestinationRecord
    ) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        members = [
            {"kind": member.kind.value, "target": member.target, "label": member.label}
            for member in row.members
        ]
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO transfer_destinations (
                    destination_id, tenant_id, customer_id, kind, label, target,
                    members_json, no_answer_seconds, status, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    kind = VALUES(kind),
                    label = VALUES(label),
                    target = VALUES(target),
                    members_json = VALUES(members_json),
                    no_answer_seconds = VALUES(no_answer_seconds),
                    status = VALUES(status),
                    updated_at = VALUES(updated_at)
                """,
                (
                    str(row.destination_id),
                    str(mysql.tenant_id),
                    str(row.customer_id),
                    row.kind.value,
                    row.label,
                    row.target,
                    json.dumps(members),
                    row.no_answer_seconds,
                    row.status.value,
                    row.created_at,
                    row.updated_at,
                ),
            )

    def get_destination(
        self, connection: TenantConnection, destination_id: uuid.UUID
    ) -> TransferDestinationRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT destination_id, tenant_id, customer_id, kind, label, target,
                       members_json, no_answer_seconds, status, created_at, updated_at
                FROM transfer_destinations
                WHERE destination_id = %s AND tenant_id = %s
                """,
                (str(destination_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._destination_row(mysql, row)

    def list_destinations(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
    ) -> list[TransferDestinationRecord]:
        mysql = self._as_mysql(connection)
        clauses = ["tenant_id = %s"]
        params: list[object] = [str(mysql.tenant_id)]
        if customer_id is not None:
            clauses.append("customer_id = %s")
            params.append(str(customer_id))
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT destination_id, tenant_id, customer_id, kind, label, target,
                       members_json, no_answer_seconds, status, created_at, updated_at
                FROM transfer_destinations
                WHERE {" AND ".join(clauses)}
                ORDER BY label
                """,
                params,
            )
            rows = cursor.fetchall()
        return [self._destination_row(mysql, row) for row in rows]

    def put_voicemail(
        self, connection: TenantConnection, row: VoicemailMessageRecord
    ) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO voicemail_messages (
                    message_id, tenant_id, customer_id, agent_id, call_id, direction,
                    status, object_ref, duration_seconds, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    object_ref = VALUES(object_ref),
                    duration_seconds = VALUES(duration_seconds),
                    updated_at = VALUES(updated_at)
                """,
                (
                    str(row.message_id),
                    str(mysql.tenant_id),
                    str(row.customer_id),
                    str(row.agent_id),
                    str(row.call_id),
                    row.direction.value,
                    row.status.value,
                    row.object_ref,
                    row.duration_seconds,
                    row.created_at,
                    row.updated_at,
                ),
            )

    def get_voicemail(
        self, connection: TenantConnection, message_id: uuid.UUID
    ) -> VoicemailMessageRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT message_id, tenant_id, customer_id, agent_id, call_id, direction,
                       status, object_ref, duration_seconds, created_at, updated_at
                FROM voicemail_messages
                WHERE message_id = %s AND tenant_id = %s
                """,
                (str(message_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._voicemail_row(mysql, row)

    def list_voicemail(
        self,
        connection: TenantConnection,
        *,
        call_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[VoicemailMessageRecord]:
        mysql = self._as_mysql(connection)
        clauses = ["tenant_id = %s"]
        params: list[object] = [str(mysql.tenant_id)]
        if call_id is not None:
            clauses.append("call_id = %s")
            params.append(str(call_id))
        if customer_id is not None:
            clauses.append("customer_id = %s")
            params.append(str(customer_id))
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT message_id, tenant_id, customer_id, agent_id, call_id, direction,
                       status, object_ref, duration_seconds, created_at, updated_at
                FROM voicemail_messages
                WHERE {" AND ".join(clauses)}
                ORDER BY created_at DESC
                """,
                params,
            )
            rows = cursor.fetchall()
        return [self._voicemail_row(mysql, row) for row in rows]

    def _call_row(self, mysql: MysqlConnection, row) -> TenantCallRecord:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return TenantCallRecord(
            call_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            agent_id=uuid.UUID(str(row[3])),
            phone_number_id=uuid.UUID(str(row[4])) if row[4] else None,
            e164=str(row[5]),
            edge_call_id=str(row[6]),
            sip_call_id=str(row[7]),
            direction=CallDirection(str(row[8])),
            status=CallStatus(str(row[9])),
            billed_minutes=int(row[10]),
            duration_seconds=int(row[11]),
            end_reason=str(row[12]),
            started_at=row[13],
            ended_at=row[14],
            remote_e164=str(row[15] or "") if len(row) > 15 else "",
            transfer_destination_id=(
                uuid.UUID(str(row[16])) if len(row) > 16 and row[16] else None
            ),
            voicemail_status=str(row[17] or "") if len(row) > 17 else "",
        )

    def _destination_row(self, mysql: MysqlConnection, row) -> TransferDestinationRecord:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        try:
            parsed = json.loads(row[6] or "[]")
        except json.JSONDecodeError:
            parsed = []
        members = tuple(
            TransferMemberRecord(
                kind=DestinationKind(str(item.get("kind"))),
                target=str(item.get("target") or ""),
                label=str(item.get("label") or ""),
            )
            for item in parsed
            if type(item) is dict
        )
        return TransferDestinationRecord(
            destination_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            kind=DestinationKind(str(row[3])),
            label=str(row[4]),
            target=str(row[5]),
            members=members,
            no_answer_seconds=int(row[7]),
            status=DestinationStatus(str(row[8])),
            created_at=row[9],
            updated_at=row[10],
        )

    def _voicemail_row(self, mysql: MysqlConnection, row) -> VoicemailMessageRecord:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return VoicemailMessageRecord(
            message_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            agent_id=uuid.UUID(str(row[3])),
            call_id=uuid.UUID(str(row[4])),
            direction=VoicemailDirection(str(row[5])),
            status=VoicemailStatus(str(row[6])),
            object_ref=str(row[7]),
            duration_seconds=int(row[8]),
            created_at=row[9],
            updated_at=row[10],
        )

    def put_artifact(
        self, connection: TenantConnection, row: TenantArtifactRecord
    ) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO recording_artifacts (
                    artifact_id, tenant_id, customer_id, call_id, kind, object_key,
                    content_type, size_bytes, checksum, status, legal_hold,
                    retention_until, provider_ref, created_at, available_at, deleted_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    legal_hold = VALUES(legal_hold),
                    available_at = VALUES(available_at),
                    deleted_at = VALUES(deleted_at)
                """,
                (
                    str(row.artifact_id),
                    str(mysql.tenant_id),
                    str(row.customer_id),
                    str(row.call_id),
                    row.kind.value,
                    row.object_key,
                    row.content_type,
                    row.size_bytes,
                    row.checksum,
                    row.status.value,
                    1 if row.legal_hold else 0,
                    row.retention_until,
                    row.provider_ref,
                    row.created_at,
                    row.available_at,
                    row.deleted_at,
                ),
            )

    def get_artifact(
        self, connection: TenantConnection, artifact_id: uuid.UUID
    ) -> TenantArtifactRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT artifact_id, tenant_id, customer_id, call_id, kind, object_key,
                       content_type, size_bytes, checksum, status, legal_hold,
                       retention_until, provider_ref, created_at, available_at, deleted_at
                FROM recording_artifacts
                WHERE artifact_id = %s AND tenant_id = %s
                """,
                (str(artifact_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._artifact_row(mysql, row)

    def list_artifacts(
        self,
        connection: TenantConnection,
        *,
        call_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantArtifactRecord]:
        mysql = self._as_mysql(connection)
        clauses = ["tenant_id = %s"]
        params: list[object] = [str(mysql.tenant_id)]
        if call_id is not None:
            clauses.append("call_id = %s")
            params.append(str(call_id))
        if customer_id is not None:
            clauses.append("customer_id = %s")
            params.append(str(customer_id))
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT artifact_id, tenant_id, customer_id, call_id, kind, object_key,
                       content_type, size_bytes, checksum, status, legal_hold,
                       retention_until, provider_ref, created_at, available_at, deleted_at
                FROM recording_artifacts
                WHERE {" AND ".join(clauses)}
                ORDER BY created_at DESC
                """,
                params,
            )
            rows = cursor.fetchall()
        return [self._artifact_row(mysql, row) for row in rows]

    def _artifact_row(self, mysql: MysqlConnection, row) -> TenantArtifactRecord:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return TenantArtifactRecord(
            artifact_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            call_id=uuid.UUID(str(row[3])),
            kind=ArtifactKind(str(row[4])),
            object_key=str(row[5]),
            content_type=str(row[6]),
            size_bytes=int(row[7]),
            checksum=str(row[8]),
            status=ArtifactStatus(str(row[9])),
            legal_hold=bool(row[10]),
            retention_until=row[11],
            provider_ref=str(row[12]),
            created_at=row[13],
            available_at=row[14],
            deleted_at=row[15],
        )

    def put_connection(
        self, connection: TenantConnection, row: TenantConnectionRecord
    ) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO integration_connections (
                    connection_id, tenant_id, customer_id, provider, status,
                    secret_ref, display_name, created_at, updated_at, revoked_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    secret_ref = VALUES(secret_ref),
                    display_name = VALUES(display_name),
                    updated_at = VALUES(updated_at),
                    revoked_at = VALUES(revoked_at)
                """,
                (
                    str(row.connection_id),
                    str(mysql.tenant_id),
                    str(row.customer_id),
                    row.provider.value,
                    row.status.value,
                    row.secret_ref,
                    row.display_name,
                    row.created_at,
                    row.updated_at,
                    row.revoked_at,
                ),
            )

    def get_connection(
        self, connection: TenantConnection, connection_id: uuid.UUID
    ) -> TenantConnectionRecord | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT connection_id, tenant_id, customer_id, provider, status,
                       secret_ref, display_name, created_at, updated_at, revoked_at
                FROM integration_connections
                WHERE connection_id = %s AND tenant_id = %s
                """,
                (str(connection_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        return self._connection_row(mysql, row) if row else None

    def list_connections(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantConnectionRecord]:
        mysql = self._as_mysql(connection)
        clauses = ["tenant_id = %s"]
        params: list[object] = [str(mysql.tenant_id)]
        if customer_id is not None:
            clauses.append("customer_id = %s")
            params.append(str(customer_id))
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT connection_id, tenant_id, customer_id, provider, status,
                       secret_ref, display_name, created_at, updated_at, revoked_at
                FROM integration_connections
                WHERE {" AND ".join(clauses)}
                ORDER BY created_at DESC
                """,
                params,
            )
            rows = cursor.fetchall()
        return [self._connection_row(mysql, row) for row in rows]

    def put_settings(
        self, connection: TenantConnection, row: TenantIntegrationSettings
    ) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO integration_settings (
                    customer_id, tenant_id, self_service, updated_at
                ) VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    self_service = VALUES(self_service),
                    updated_at = VALUES(updated_at)
                """,
                (
                    str(row.customer_id),
                    str(mysql.tenant_id),
                    1 if row.self_service else 0,
                    row.updated_at,
                ),
            )

    def get_settings(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> TenantIntegrationSettings | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT customer_id, tenant_id, self_service, updated_at
                FROM integration_settings
                WHERE customer_id = %s AND tenant_id = %s
                """,
                (str(customer_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return TenantIntegrationSettings(
            customer_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            self_service=bool(row[2]),
            updated_at=row[3],
        )

    def put_endpoint(
        self, connection: TenantConnection, row: TenantWebhookEndpoint
    ) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO webhook_endpoints (
                    endpoint_id, tenant_id, customer_id, url, secret_ref, status,
                    events_json, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    url = VALUES(url),
                    secret_ref = VALUES(secret_ref),
                    status = VALUES(status),
                    events_json = VALUES(events_json),
                    updated_at = VALUES(updated_at)
                """,
                (
                    str(row.endpoint_id),
                    str(mysql.tenant_id),
                    str(row.customer_id),
                    row.url,
                    row.secret_ref,
                    row.status.value,
                    json.dumps(list(row.events)),
                    row.created_at,
                    row.updated_at,
                ),
            )

    def get_endpoint(
        self, connection: TenantConnection, endpoint_id: uuid.UUID
    ) -> TenantWebhookEndpoint | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT endpoint_id, tenant_id, customer_id, url, secret_ref, status,
                       events_json, created_at, updated_at
                FROM webhook_endpoints
                WHERE endpoint_id = %s AND tenant_id = %s
                """,
                (str(endpoint_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        return self._endpoint_row(mysql, row) if row else None

    def list_endpoints(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantWebhookEndpoint]:
        mysql = self._as_mysql(connection)
        clauses = ["tenant_id = %s"]
        params: list[object] = [str(mysql.tenant_id)]
        if customer_id is not None:
            clauses.append("customer_id = %s")
            params.append(str(customer_id))
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT endpoint_id, tenant_id, customer_id, url, secret_ref, status,
                       events_json, created_at, updated_at
                FROM webhook_endpoints
                WHERE {" AND ".join(clauses)}
                ORDER BY created_at DESC
                """,
                params,
            )
            rows = cursor.fetchall()
        return [self._endpoint_row(mysql, row) for row in rows]

    def put_delivery(
        self, connection: TenantConnection, row: TenantWebhookDelivery
    ) -> None:
        mysql = self._as_mysql(connection)
        if row.tenant_id != mysql.tenant_id:
            raise isolation_violation()
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO webhook_deliveries (
                    delivery_id, tenant_id, customer_id, endpoint_id, event_id,
                    event_type, object_id, status, attempt_count, response_code,
                    last_error, created_at, next_attempt_at, delivered_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    attempt_count = VALUES(attempt_count),
                    response_code = VALUES(response_code),
                    last_error = VALUES(last_error),
                    next_attempt_at = VALUES(next_attempt_at),
                    delivered_at = VALUES(delivered_at)
                """,
                (
                    str(row.delivery_id),
                    str(mysql.tenant_id),
                    str(row.customer_id),
                    str(row.endpoint_id),
                    str(row.event_id),
                    row.event_type,
                    str(row.object_id),
                    row.status.value,
                    row.attempt_count,
                    row.response_code,
                    row.last_error,
                    row.created_at,
                    row.next_attempt_at,
                    row.delivered_at,
                ),
            )

    def get_delivery(
        self, connection: TenantConnection, delivery_id: uuid.UUID
    ) -> TenantWebhookDelivery | None:
        mysql = self._as_mysql(connection)
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                """
                SELECT delivery_id, tenant_id, customer_id, endpoint_id, event_id,
                       event_type, object_id, status, attempt_count, response_code,
                       last_error, created_at, next_attempt_at, delivered_at
                FROM webhook_deliveries
                WHERE delivery_id = %s AND tenant_id = %s
                """,
                (str(delivery_id), str(mysql.tenant_id)),
            )
            row = cursor.fetchone()
        return self._delivery_row(mysql, row) if row else None

    def list_deliveries(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
        endpoint_id: uuid.UUID | None = None,
    ) -> list[TenantWebhookDelivery]:
        mysql = self._as_mysql(connection)
        clauses = ["tenant_id = %s"]
        params: list[object] = [str(mysql.tenant_id)]
        if customer_id is not None:
            clauses.append("customer_id = %s")
            params.append(str(customer_id))
        if endpoint_id is not None:
            clauses.append("endpoint_id = %s")
            params.append(str(endpoint_id))
        with mysql.raw.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT delivery_id, tenant_id, customer_id, endpoint_id, event_id,
                       event_type, object_id, status, attempt_count, response_code,
                       last_error, created_at, next_attempt_at, delivered_at
                FROM webhook_deliveries
                WHERE {" AND ".join(clauses)}
                ORDER BY created_at DESC
                """,
                params,
            )
            rows = cursor.fetchall()
        return [self._delivery_row(mysql, row) for row in rows]

    def _connection_row(self, mysql: MysqlConnection, row) -> TenantConnectionRecord:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return TenantConnectionRecord(
            connection_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            provider=ProviderKind(str(row[3])),
            status=ConnectionStatus(str(row[4])),
            secret_ref=str(row[5]),
            display_name=str(row[6]),
            created_at=row[7],
            updated_at=row[8],
            revoked_at=row[9],
        )

    def _endpoint_row(self, mysql: MysqlConnection, row) -> TenantWebhookEndpoint:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        events = json.loads(row[6] or "[]")
        return TenantWebhookEndpoint(
            endpoint_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            url=str(row[3]),
            secret_ref=str(row[4]),
            status=EndpointStatus(str(row[5])),
            events=tuple(str(item) for item in events),
            created_at=row[7],
            updated_at=row[8],
        )

    def _delivery_row(self, mysql: MysqlConnection, row) -> TenantWebhookDelivery:
        tenant_id = uuid.UUID(str(row[1]))
        if tenant_id != mysql.tenant_id:
            raise isolation_violation()
        return TenantWebhookDelivery(
            delivery_id=uuid.UUID(str(row[0])),
            tenant_id=tenant_id,
            customer_id=uuid.UUID(str(row[2])),
            endpoint_id=uuid.UUID(str(row[3])),
            event_id=uuid.UUID(str(row[4])),
            event_type=str(row[5]),
            object_id=uuid.UUID(str(row[6])),
            status=DeliveryStatus(str(row[7])),
            attempt_count=int(row[8]),
            response_code=int(row[9]) if row[9] is not None else None,
            last_error=str(row[10] or ""),
            created_at=row[11],
            next_attempt_at=row[12],
            delivered_at=row[13],
        )

    def _applied_versions(self, connection: MysqlConnection) -> list[str]:
        with connection.raw.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tenant_schema_migrations (
                    version VARCHAR(64) PRIMARY KEY,
                    applied_at DATETIME(6) NOT NULL
                )
                """
            )
            cursor.execute("SELECT version FROM tenant_schema_migrations")
            return [str(row[0]) for row in cursor.fetchall()]

    def _as_mysql(self, connection: TenantConnection) -> MysqlConnection:
        if not isinstance(connection, MysqlConnection):
            raise isolation_violation()
        return connection

    def _ssl(self, target: ConnectionTarget):
        if target.tls_required:
            return {}
        return None


def _safe_ident(name: str) -> str:
    if not name or any(ch in name for ch in "`;/\\ \n\r\t"):
        raise DomainError("invalid_database_name", "Database name is invalid.")
    return name


def bootstrap_mysql_schema(runtime: MysqlRuntime, target: ConnectionTarget) -> str:
    runtime.ensure_database(target)
    connection = runtime.open(target)
    try:
        runtime.apply(connection, CURRENT_VERSION)
        runtime.verify(connection, CURRENT_VERSION)
        return CURRENT_VERSION
    finally:
        runtime.close(connection)
