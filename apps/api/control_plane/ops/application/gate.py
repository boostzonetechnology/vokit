from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings

from control_plane.ops.application.catalog import all_items
from control_plane.ops.domain.policies import parse_attestation
from control_plane.ops.domain.types import (
    EvidenceKind,
    GateCheck,
    GateMode,
    GateReport,
    GateVerdict,
)
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.ops")


class ProductionReadiness:
    def __init__(self, repo_root: Path, environ: dict[str, str]) -> None:
        self._root = repo_root
        self._environ = environ
        self._tests = self._load_tests()

    def _load_tests(self) -> str:
        tests = self._root / "apps" / "api" / "tests"
        if not tests.is_dir():
            return ""
        chunks: list[str] = []
        for path in tests.glob("test_*.py"):
            chunks.append(path.read_text(encoding="utf-8"))
        return "\n".join(chunks)

    def _check(self, mode: GateMode) -> list[GateCheck]:
        rows: list[GateCheck] = []
        for item in all_items():
            if mode is GateMode.LAB and item.kind is EvidenceKind.ATTESTATION:
                continue
            if item.kind is EvidenceKind.FILE_EXISTS:
                path = self._root / item.evidence
                rows.append(
                    GateCheck(
                        item,
                        path.is_file(),
                        str(path) if path.is_file() else "missing file",
                    )
                )
            elif item.kind is EvidenceKind.TEST_NAME:
                found = f"def {item.evidence}(" in self._tests
                rows.append(
                    GateCheck(
                        item,
                        found,
                        "test present" if found else "test missing",
                    )
                )
            else:
                dated = parse_attestation(self._environ.get(item.evidence, ""))
                rows.append(
                    GateCheck(
                        item,
                        dated is not None,
                        dated or "missing dated attestation",
                    )
                )
        return rows

    def execute(self, mode: GateMode) -> GateReport:
        launch_flag = (self._environ.get("VOKIT_LAUNCH_GO") or "").strip().lower()
        checks = self._check(mode)
        required = [row for row in checks if row.item.required_for_go]
        all_pass = all(row.passed for row in required)
        if launch_flag in {"1", "true", "yes", "on"} and not all_pass:
            log_event(
                logger,
                "production.gate.launch_flag_ignored",
                outcome="denied",
                mode=mode.value,
            )
        if mode is GateMode.LAB:
            verdict = GateVerdict.LAB_READY if all_pass else GateVerdict.NO_GO
        else:
            verdict = GateVerdict.GO if all_pass else GateVerdict.NO_GO
        report = GateReport(mode, verdict, tuple(checks))
        log_event(
            logger,
            "production.gate.evaluated",
            outcome="success" if all_pass else "denied",
            mode=mode.value,
            verdict=verdict.value,
        )
        return report


def repo_root() -> Path:
    base = Path(settings.BASE_DIR)
    return base.parent.parent
