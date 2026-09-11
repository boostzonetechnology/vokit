from __future__ import annotations

import pytest

from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.application.backup import (
    assert_snapshot_has_no_secrets,
    snapshot_from_dict,
)
from control_plane.tenancy.application.provision_tenant import ProvisionTenantCommand
from control_plane.tenancy.infrastructure.container import (
    backup_control_plane,
    backup_tenant,
    isolation_records,
    provisioner,
    restore_tenant,
    tenant_repo,
)
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7


def _provision(name: str, db_name: str):
    return provisioner().execute(
        ProvisionTenantCommand(
            display_name=name,
            host="127.0.0.1",
            port=3306,
            name=db_name,
            db_username=f"u_{db_name}",
            db_password="TenantDbPass12!",
            tls_required=False,
        )
    )


def _put(tenant_id, object_id, payload: str):
    return isolation_records().put(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=tenant_id,
        claimed_tenant_id=None,
        permissions=frozenset(),
        object_id=object_id,
        payload=payload,
    )


def _get(tenant_id, object_id):
    return isolation_records().get(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=tenant_id,
        claimed_tenant_id=None,
        permissions=frozenset(),
        object_id=object_id,
    )


@pytest.mark.django_db
def test_restore_one_tenant_does_not_touch_the_other() -> None:
    agency_a = _provision("Backup A", "bak_a")
    agency_b = _provision("Backup B", "bak_b")
    object_a = new_uuid7()
    object_b = new_uuid7()
    _put(agency_a.id, object_a, "alpha-original")
    _put(agency_b.id, object_b, "bravo-original")
    snapshot = backup_tenant().execute(agency_a.id)
    document = snapshot.to_public_dict()
    assert_snapshot_has_no_secrets(document)
    assert "vault:tenant_db" == document["secret_ref"]
    assert "127.0.0.1" not in str(document["payload"])
    _put(agency_a.id, object_a, "alpha-mutated")
    _put(agency_b.id, object_b, "bravo-mutated")
    restore_tenant().execute(agency_a.id, snapshot)
    assert _get(agency_a.id, object_a).payload == "alpha-original"
    assert _get(agency_b.id, object_b).payload == "bravo-mutated"
    with pytest.raises(DomainError) as exc:
        restore_tenant().execute(agency_b.id, snapshot)
    assert exc.value.code == "tenant_restore_mismatch"
    assert _get(agency_b.id, object_b).payload == "bravo-mutated"


@pytest.mark.django_db
def test_control_plane_restore_is_tenant_scoped() -> None:
    agency_a = _provision("Registry A", "reg_a")
    agency_b = _provision("Registry B", "reg_b")
    document = backup_control_plane().execute()
    assert_snapshot_has_no_secrets(document)
    tenant_repo().update(tenant_repo().get(agency_a.id).with_agency(display_name="Mutated A"))
    tenant_repo().update(tenant_repo().get(agency_b.id).with_agency(display_name="Mutated B"))
    backup_control_plane().restore_tenant_row(agency_a.id, document)
    assert tenant_repo().get(agency_a.id).display_name == "Registry A"
    assert tenant_repo().get(agency_b.id).display_name == "Mutated B"


@pytest.mark.django_db
def test_missing_tenant_backup_fails_closed() -> None:
    with pytest.raises(DomainError) as exc:
        backup_tenant().execute(new_uuid7())
    assert exc.value.code == "tenant_route_denied"
    with pytest.raises(DomainError):
        snapshot_from_dict({"plane": "control", "tenants": []})
