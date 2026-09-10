from __future__ import annotations

import os
import uuid

import pytest

from shared_kernel.ids import new_uuid7
from tenant.runtime.domain import IsolationRecord
from tenant.runtime.mysql import MysqlRuntime
from tenant.runtime.ports import ConnectionTarget
from tenant.schema import CURRENT_VERSION

mysql_enabled = os.environ.get("VOKIT_MYSQL_ISOLATION") == "1"

pytestmark = [
    pytest.mark.mysql,
    pytest.mark.skipif(
        not mysql_enabled,
        reason="Set VOKIT_MYSQL_ISOLATION=1 with two tenant MySQL databases",
    ),
]


def _target(tenant_id: uuid.UUID, name: str) -> ConnectionTarget:
    return ConnectionTarget(
        tenant_id=tenant_id,
        database_id=new_uuid7(),
        host=os.environ.get("TENANT_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("TENANT_DB_PORT", "3306")),
        name=name,
        secret_ref=os.environ.get("TENANT_DB_PASSWORD_REF", "TENANT_DB_PASSWORD"),
        tls_required=False,
    )


def test_mysql_same_object_id_stays_on_current_tenant_db() -> None:
    os.environ.setdefault("TENANT_DB_PASSWORD", os.environ.get("TENANT_DB_PASSWORD", "vokit_ci"))
    runtime = MysqlRuntime(user=os.environ.get("TENANT_DB_USER", "vokit"))
    tenant_a = new_uuid7()
    tenant_b = new_uuid7()
    object_id = new_uuid7()
    target_a = _target(tenant_a, os.environ.get("TENANT_DB_NAME_A", "vokit_tenant_a"))
    target_b = _target(tenant_b, os.environ.get("TENANT_DB_NAME_B", "vokit_tenant_b"))
    runtime.ensure_database(target_a)
    runtime.ensure_database(target_b)
    for target in (target_a, target_b):
        connection = runtime.open(target)
        try:
            runtime.apply(connection, CURRENT_VERSION)
            runtime.verify(connection, CURRENT_VERSION)
        finally:
            runtime.close(connection)
    conn_a = runtime.open(target_a)
    conn_b = runtime.open(target_b)
    try:
        runtime.upsert(
            conn_a,
            IsolationRecord(object_id=object_id, tenant_id=tenant_a, payload="mysql-a"),
        )
        runtime.upsert(
            conn_b,
            IsolationRecord(object_id=object_id, tenant_id=tenant_b, payload="mysql-b"),
        )
        assert runtime.get(conn_a, object_id).payload == "mysql-a"
        assert runtime.get(conn_b, object_id).payload == "mysql-b"
    finally:
        runtime.close(conn_a)
        runtime.close(conn_b)
