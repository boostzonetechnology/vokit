from __future__ import annotations

import uuid

import pytest

from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.application.ports import TenantDatabaseRecord, TenantRecord
from control_plane.tenancy.domain.types import DatabaseStatus, TenantStatus
from control_plane.tenancy.infrastructure.container import reset_runtime, runtime
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from tenant.runtime.domain import IsolationRecord, JobContext
from tenant.runtime.memory import MemoryRuntime
from tenant.runtime.ports import ConnectionTarget
from tenant.runtime.records import IsolationRecordService
from tenant.runtime.router import TenantRouter
from tenant.schema import CURRENT_VERSION


class _MapRepo:
    def __init__(self) -> None:
        self.tenants: dict[uuid.UUID, TenantRecord] = {}
        self.databases: dict[uuid.UUID, TenantDatabaseRecord] = {}

    def get(self, tenant_id: uuid.UUID) -> TenantRecord | None:
        return self.tenants.get(tenant_id)

    def list(self) -> list[TenantRecord]:
        return list(self.tenants.values())

    def create(self, tenant: TenantRecord) -> None:
        self.tenants[tenant.id] = tenant

    def update_status(self, tenant_id: uuid.UUID, status: TenantStatus) -> None:
        current = self.tenants[tenant_id]
        self.tenants[tenant_id] = TenantRecord(current.id, current.display_name, status)

    def get_for_tenant(self, tenant_id: uuid.UUID) -> TenantDatabaseRecord | None:
        return self.databases.get(tenant_id)

    def create_db(self, record: TenantDatabaseRecord) -> None:
        self.databases[record.tenant_id] = record

    def update(self, record: TenantDatabaseRecord) -> None:
        self.databases[record.tenant_id] = record


def _target(tenant_id: uuid.UUID, name: str) -> ConnectionTarget:
    return ConnectionTarget(
        tenant_id=tenant_id,
        database_id=new_uuid7(),
        host="127.0.0.1",
        port=3306,
        name=name,
        secret_ref="TENANT_DB_PASSWORD",
        tls_required=False,
    )


def _ready(maps: _MapRepo, tenant_id: uuid.UUID, name: str) -> ConnectionTarget:
    maps.create(TenantRecord(tenant_id, name, TenantStatus.READY))
    target = _target(tenant_id, name)
    maps.create_db(
        TenantDatabaseRecord(
            id=target.database_id,
            tenant_id=tenant_id,
            host=target.host,
            port=target.port,
            name=target.name,
            secret_ref=target.secret_ref,
            tls_required=False,
            status=DatabaseStatus.HEALTHY,
            schema_version=CURRENT_VERSION,
        )
    )
    return target


@pytest.fixture
def harness() -> tuple[MemoryRuntime, _MapRepo, IsolationRecordService]:
    reset_runtime()
    engine = runtime()
    assert isinstance(engine, MemoryRuntime)
    maps = _MapRepo()
    service = IsolationRecordService(TenantRouter(maps, maps, engine), engine)
    return engine, maps, service


def test_same_object_id_resolves_only_in_current_tenant(harness) -> None:
    engine, maps, service = harness
    tenant_a = new_uuid7()
    tenant_b = new_uuid7()
    object_id = new_uuid7()
    _ready(maps, tenant_a, "tenant_a")
    _ready(maps, tenant_b, "tenant_b")
    service.put(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=tenant_a,
        claimed_tenant_id=tenant_b,
        permissions=frozenset(),
        object_id=object_id,
        payload="alpha",
    )
    service.put(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=tenant_b,
        claimed_tenant_id=tenant_a,
        permissions=frozenset(),
        object_id=object_id,
        payload="bravo",
    )
    assert (
        service.get(
            principal_type=PrincipalType.AGENCY,
            membership_tenant_id=tenant_a,
            claimed_tenant_id=tenant_b,
            permissions=frozenset(),
            object_id=object_id,
        ).payload
        == "alpha"
    )
    assert (
        service.get(
            principal_type=PrincipalType.AGENCY,
            membership_tenant_id=tenant_b,
            claimed_tenant_id=None,
            permissions=frozenset(),
            object_id=object_id,
        ).payload
        == "bravo"
    )


def test_missing_mapping_fails_closed(harness) -> None:
    _engine, maps, service = harness
    tenant_id = new_uuid7()
    maps.create(TenantRecord(tenant_id, "orphan", TenantStatus.READY))
    with pytest.raises(DomainError) as exc:
        service.get(
            principal_type=PrincipalType.AGENCY,
            membership_tenant_id=tenant_id,
            claimed_tenant_id=None,
            permissions=frozenset(),
            object_id=new_uuid7(),
        )
    assert exc.value.code == "tenant_route_denied"


def test_disabled_tenant_cannot_be_routed(harness) -> None:
    _engine, maps, service = harness
    tenant_id = new_uuid7()
    _ready(maps, tenant_id, "suspended")
    maps.update_status(tenant_id, TenantStatus.SUSPENDED)
    with pytest.raises(DomainError) as exc:
        service.get(
            principal_type=PrincipalType.AGENCY,
            membership_tenant_id=tenant_id,
            claimed_tenant_id=None,
            permissions=frozenset(),
            object_id=new_uuid7(),
        )
    assert exc.value.code == "tenant_route_denied"


def test_outage_does_not_fall_back(harness) -> None:
    engine, maps, service = harness
    tenant_a = new_uuid7()
    tenant_b = new_uuid7()
    object_id = new_uuid7()
    _ready(maps, tenant_a, "down_a")
    _ready(maps, tenant_b, "up_b")
    service.put(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=tenant_b,
        claimed_tenant_id=None,
        permissions=frozenset(),
        object_id=object_id,
        payload="safe",
    )
    engine.mark_down("down_a")
    with pytest.raises(DomainError) as exc:
        service.get(
            principal_type=PrincipalType.AGENCY,
            membership_tenant_id=tenant_a,
            claimed_tenant_id=tenant_b,
            permissions=frozenset(),
            object_id=object_id,
        )
    assert exc.value.code == "tenant_db_unavailable"
    assert (
        service.get(
            principal_type=PrincipalType.AGENCY,
            membership_tenant_id=tenant_b,
            claimed_tenant_id=None,
            permissions=frozenset(),
            object_id=object_id,
        ).payload
        == "safe"
    )


def test_worker_job_cannot_cross_tenant(harness) -> None:
    _engine, maps, service = harness
    tenant_a = new_uuid7()
    tenant_b = new_uuid7()
    object_id = new_uuid7()
    _ready(maps, tenant_a, "job_a")
    _ready(maps, tenant_b, "job_b")
    service.put(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=tenant_b,
        claimed_tenant_id=None,
        permissions=frozenset(),
        object_id=object_id,
        payload="secret-b",
    )
    with pytest.raises(DomainError) as exc:
        service.get_for_job(JobContext(tenant_id=tenant_a, correlation_id="job-1"), object_id)
    assert exc.value.code == "not_found"


def test_pool_cannot_leak_tenant_context(harness) -> None:
    engine, maps, _service = harness
    tenant_a = new_uuid7()
    tenant_b = new_uuid7()
    target_a = _ready(maps, tenant_a, "pool_a")
    target_b = _ready(maps, tenant_b, "pool_b")
    conn_a = engine.acquire(target_a)
    conn_b = engine.acquire(target_b)
    assert conn_a.tenant_id == tenant_a
    assert conn_b.tenant_id == tenant_b
    assert engine.checked_out_tenant_ids() == {tenant_a, tenant_b}
    with pytest.raises(DomainError) as exc:
        engine.upsert(
            conn_a,
            IsolationRecord(object_id=new_uuid7(), tenant_id=tenant_b, payload="nope"),
        )
    assert exc.value.code == "tenant_isolation_violation"
    engine.release(conn_a)
    engine.release(conn_b)
