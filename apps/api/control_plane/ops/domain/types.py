from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GateMode(StrEnum):
    LAB = "lab"
    PRODUCTION = "production"


class GateVerdict(StrEnum):
    LAB_READY = "LAB_READY"
    GO = "GO"
    NO_GO = "NO_GO"


class EvidenceKind(StrEnum):
    TEST_NAME = "test_name"
    FILE_EXISTS = "file_exists"
    ATTESTATION = "attestation"


@dataclass(frozen=True, slots=True)
class GateItem:
    item_id: str
    section: str
    kind: EvidenceKind
    required_for_go: bool
    evidence: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class GateCheck:
    item: GateItem
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class GateReport:
    mode: GateMode
    verdict: GateVerdict
    checks: tuple[GateCheck, ...]

    def to_public_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "verdict": self.verdict.value,
            "passed": sum(1 for row in self.checks if row.passed),
            "failed": sum(1 for row in self.checks if not row.passed),
            "checks": [
                {
                    "id": row.item.item_id,
                    "section": row.item.section,
                    "kind": row.item.kind.value,
                    "passed": row.passed,
                    "detail": row.detail,
                    "evidence": row.item.evidence,
                }
                for row in self.checks
            ],
        }
