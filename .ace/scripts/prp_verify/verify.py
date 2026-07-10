#!/usr/bin/env python3
"""Orquestração por PRP: parser → checkers → resultado."""

import re
from pathlib import Path

from .checks import (
    check_components,
    check_endpoints,
    check_rf_evidence,
    check_tests,
)
from .constants import PRP_DIR
from .coverage import check_project_coverage
from .models import Finding, VerifyResult
from .parsing import (
    parse_components,
    parse_endpoints,
    parse_rf_table,
    parse_test_files,
)
from .parsing import _get_section


def verify_prp(prp_path: Path) -> VerifyResult:
    result = VerifyResult(prp=prp_path.stem)
    content = prp_path.read_text(encoding="utf-8", errors="replace")

    section2 = _get_section(content, "2")
    section5 = _get_section(content, "5")
    section6 = _get_section(content, "6")
    section9 = _get_section(content, "9")

    rf_rows, has_trace = parse_rf_table(section2)
    endpoints = parse_endpoints(section5)
    comps = parse_components(section6)
    section9_files = parse_test_files(section9)

    check_rf_evidence(rf_rows, has_trace, section9_files, result)
    check_tests(section9_files, result)
    check_components(comps, result)
    check_endpoints(endpoints, result)

    # P0: Project-wide test coverage check
    coverage_exit, coverage_findings = check_project_coverage()
    for cf in coverage_findings:
        result.findings.append(
            Finding(
                severity=cf["severity"],
                code=cf["code"],
                message=cf["message"],
                file=cf.get("file", ""),
            )
        )

    return result


def discover_prps() -> list[Path]:
    if not PRP_DIR.exists():
        return []
    out = []
    for p in sorted(PRP_DIR.glob("PRP-*.md")):
        if re.match(r"PRP-\d", p.name):
            out.append(p)
    return out


def resolve_prp_path(prp_id: str) -> Path | None:
    """Aceita 'PRP-001' ou caminho completo."""
    cand = Path(prp_id)
    if cand.exists():
        return cand
    # PRP-001 → docs/prps/PRP-001*.md
    hits = sorted(PRP_DIR.glob(f"{prp_id}*.md"))
    hits = [h for h in hits if re.match(r"PRP-\d", h.name)]
    return hits[0] if hits else None
