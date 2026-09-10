from __future__ import annotations

from control_plane.ops.domain.types import EvidenceKind, GateItem

GOVERNANCE_ITEMS: tuple[GateItem, ...] = (
    GateItem(
        "gov.srs",
        "governance",
        EvidenceKind.FILE_EXISTS,
        True,
        "docs/Vokit_V1_Agency_Platform_SRS_v1.0.md",
    ),
    GateItem(
        "gov.adr001",
        "governance",
        EvidenceKind.FILE_EXISTS,
        True,
        "docs/adr/ADR-001-tenant-database-topology.md",
    ),
    GateItem(
        "gov.adr002",
        "governance",
        EvidenceKind.FILE_EXISTS,
        True,
        "docs/adr/ADR-002-recording-storage-separation.md",
    ),
    GateItem(
        "gov.adr005",
        "governance",
        EvidenceKind.FILE_EXISTS,
        True,
        "docs/adr/ADR-005-external-kyc-provider.md",
    ),
    GateItem(
        "gov.no_customer_reassignment",
        "governance",
        EvidenceKind.TEST_NAME,
        True,
        "test_reassignment_endpoint_is_forbidden",
    ),
    GateItem(
        "gov.no_kyc_vault",
        "governance",
        EvidenceKind.TEST_NAME,
        True,
        "test_kyc_models_do_not_store_files",
    ),
)

LAB_ITEMS: tuple[GateItem, ...] = (
    GateItem(
        "lab.tenant_isolation",
        "lab",
        EvidenceKind.TEST_NAME,
        True,
        "test_same_object_id_resolves_only_in_current_tenant",
    ),
    GateItem(
        "lab.recording_matrix",
        "lab",
        EvidenceKind.TEST_NAME,
        True,
        "test_recording_negative_matrix",
    ),
    GateItem(
        "lab.finance_idempotency",
        "lab",
        EvidenceKind.TEST_NAME,
        True,
        "test_duplicate_stripe_webhook_settles_once",
    ),
    GateItem(
        "lab.sandbox_e2e",
        "lab",
        EvidenceKind.TEST_NAME,
        True,
        "test_staging_sandbox_canary_payment_and_restore",
    ),
    GateItem(
        "lab.backup_restore",
        "lab",
        EvidenceKind.TEST_NAME,
        True,
        "test_restore_one_tenant_does_not_touch_the_other",
    ),
    GateItem(
        "lab.canary",
        "lab",
        EvidenceKind.TEST_NAME,
        True,
        "test_canary_migration_then_bounded_batch",
    ),
    GateItem(
        "lab.security_review",
        "lab",
        EvidenceKind.FILE_EXISTS,
        True,
        "docs/execution/24-PHASE-17-SECURITY-REVIEW.md",
    ),
    GateItem(
        "lab.runbooks",
        "lab",
        EvidenceKind.FILE_EXISTS,
        True,
        "docs/execution/runbooks/README.md",
    ),
)

LIVE_ITEMS: tuple[GateItem, ...] = (
    GateItem(
        "live.inbound_call",
        "live",
        EvidenceKind.ATTESTATION,
        True,
        "VOKIT_EVIDENCE_LIVE_INBOUND_CALL",
        "Dated inbound canary call",
    ),
    GateItem(
        "live.outbound_call",
        "live",
        EvidenceKind.ATTESTATION,
        True,
        "VOKIT_EVIDENCE_LIVE_OUTBOUND_CALL",
        "Dated outbound canary call",
    ),
    GateItem(
        "live.payment",
        "live",
        EvidenceKind.ATTESTATION,
        True,
        "VOKIT_EVIDENCE_LIVE_PAYMENT",
        "Dated live/canary charge + commission",
    ),
    GateItem(
        "live.recording_play",
        "live",
        EvidenceKind.ATTESTATION,
        True,
        "VOKIT_EVIDENCE_LIVE_RECORDING",
        "Dated short-lived recording play",
    ),
    GateItem(
        "live.restore_drill",
        "live",
        EvidenceKind.ATTESTATION,
        True,
        "VOKIT_EVIDENCE_RESTORE_DRILL",
        "Dated control + one tenant restore",
    ),
    GateItem(
        "live.alerting",
        "live",
        EvidenceKind.ATTESTATION,
        True,
        "VOKIT_EVIDENCE_ALERTING",
        "On-call confirmed P0 pages",
    ),
    GateItem(
        "live.rollback",
        "live",
        EvidenceKind.ATTESTATION,
        True,
        "VOKIT_EVIDENCE_ROLLBACK_STAGING",
        "Rollback performed once in staging",
    ),
    GateItem(
        "live.legal",
        "live",
        EvidenceKind.ATTESTATION,
        True,
        "VOKIT_EVIDENCE_LEGAL_SIGN_OFF",
        "Compliance/legal launch sign-off",
    ),
)


def all_items() -> tuple[GateItem, ...]:
    return GOVERNANCE_ITEMS + LAB_ITEMS + LIVE_ITEMS
