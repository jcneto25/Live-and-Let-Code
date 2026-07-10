#!/usr/bin/env python3
"""code-health — parsing de relatórios de cobertura e detecção de tendências."""

import json
import sys
from pathlib import Path


def parse_coverage_report(coverage_file: Path) -> dict | None:
    """Parse coverage report from various formats.

    Supports:
    - vitest/jest: coverage/coverage-final.json
    - pytest-cov: coverage.json (via pytest-cov --cov-report=json)
    - go test: coverage.out (via go test -coverprofile)
    - lcov: lcov.info
    """
    if not coverage_file.exists():
        return None

    suffix = coverage_file.suffix.lower()

    try:
        if suffix == ".json":
            data = json.loads(coverage_file.read_text(encoding="utf-8"))

            if isinstance(data, dict) and all(
                isinstance(v, dict) and "s" in v for v in data.values()
            ):
                return _parse_vitest_coverage(data)

            if isinstance(data, dict) and "files" in data:
                return _parse_pytest_coverage(data)

            if isinstance(data, dict) and "total" in data:
                return _parse_generic_coverage(data)

        elif suffix in (".out", ".cov"):
            return _parse_go_coverage(coverage_file)

        elif suffix in (".info", ".lcov"):
            return _parse_lcov_coverage(coverage_file)

    except Exception as e:
        print(f"⚠️  Failed to parse coverage report: {e}", file=sys.stderr)
        return None

    return None


def _parse_vitest_coverage(data: dict) -> dict:
    """Parse vitest/jest coverage JSON format."""
    total_statements = 0
    covered_statements = 0
    total_branches = 0
    covered_branches = 0
    total_functions = 0
    covered_functions = 0
    total_lines = 0
    covered_lines = 0
    files = {}
    zero_coverage_files = []

    for file_path, file_data in data.items():
        if not isinstance(file_data, dict):
            continue

        s = file_data.get("s", {})
        for _, count in s.items():
            total_statements += 1
            if count > 0:
                covered_statements += 1

        b = file_data.get("b", {})
        for _, branches in b.items():
            for _, count in branches.items():
                total_branches += 1
                if count > 0:
                    covered_branches += 1

        f = file_data.get("f", {})
        for _, count in f.items():
            total_functions += 1
            if count > 0:
                covered_functions += 1

        file_lines = len(s)
        file_covered = sum(1 for c in s.values() if c > 0)
        total_lines += file_lines
        covered_lines += file_covered

        stmt_pct = round((file_covered / file_lines * 100), 1) if file_lines > 0 else 0
        files[file_path] = {
            "statements": {
                "total": file_lines,
                "covered": file_covered,
                "pct": stmt_pct,
            },
        }

        if stmt_pct == 0 and file_lines > 0:
            zero_coverage_files.append(file_path)

    return {
        "statements": {
            "total": total_statements,
            "covered": covered_statements,
            "pct": round((covered_statements / total_statements * 100), 1)
            if total_statements > 0
            else 0,
        },
        "branches": {
            "total": total_branches,
            "covered": covered_branches,
            "pct": round((covered_branches / total_branches * 100), 1)
            if total_branches > 0
            else 0,
        },
        "functions": {
            "total": total_functions,
            "covered": covered_functions,
            "pct": round((covered_functions / total_functions * 100), 1)
            if total_functions > 0
            else 0,
        },
        "lines": {
            "total": total_lines,
            "covered": covered_lines,
            "pct": round((covered_lines / total_lines * 100), 1)
            if total_lines > 0
            else 0,
        },
        "files": files,
        "zero_coverage_files": zero_coverage_files,
    }


def _parse_pytest_coverage(data: dict) -> dict:
    """Parse pytest-cov JSON format."""
    files = data.get("files", {})
    totals = data.get("totals", {})

    return {
        "statements": {
            "total": totals.get("num_statements", 0),
            "covered": totals.get("covered_lines", 0),
            "pct": totals.get("percent_covered", 0),
        },
        "lines": {
            "total": totals.get("num_statements", 0),
            "covered": totals.get("covered_lines", 0),
            "pct": totals.get("percent_covered", 0),
        },
        "files": {},
        "zero_coverage_files": [],
    }


def _parse_generic_coverage(data: dict) -> dict:
    """Parse generic coverage JSON with totals."""
    total = data.get("total", {})
    return {
        "statements": {
            "total": total.get("statements", 0),
            "covered": total.get("covered", 0),
            "pct": total.get("pct", 0),
        },
        "files": {},
        "zero_coverage_files": [],
    }


def _parse_go_coverage(coverage_file: Path) -> dict:
    """Parse go test -coverprofile output."""
    content = coverage_file.read_text(encoding="utf-8")
    total = 0
    covered = 0

    for line in content.splitlines():
        if line.startswith("mode:") or not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 3:
            try:
                count = int(parts[2])
                total += 1
                if count > 0:
                    covered += 1
            except ValueError:
                pass

    return {
        "statements": {
            "total": total,
            "covered": covered,
            "pct": round((covered / total * 100), 1) if total > 0 else 0,
        },
        "files": {},
        "zero_coverage_files": [],
    }


def _parse_lcov_coverage(coverage_file: Path) -> dict:
    """Parse lcov format coverage."""
    content = coverage_file.read_text(encoding="utf-8")
    total = 0
    covered = 0

    for line in content.splitlines():
        if line.startswith("DA:"):
            parts = line[3:].split(",")
            if len(parts) >= 2:
                try:
                    count = int(parts[1])
                    total += 1
                    if count > 0:
                        covered += 1
                except ValueError:
                    pass

    return {
        "statements": {
            "total": total,
            "covered": covered,
            "pct": round((covered / total * 100), 1) if total > 0 else 0,
        },
        "files": {},
        "zero_coverage_files": [],
    }


def load_coverage_history(history_file: Path) -> list[dict]:
    """Load coverage history from JSON file."""
    if not history_file.exists():
        return []
    try:
        return json.loads(history_file.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_coverage_history(
    history_file: Path, history: list[dict], max_entries: int = 100
):
    """Save coverage history to JSON file, keeping only recent entries."""
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history = history[-max_entries:]
    history_file.write_text(
        json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def check_coverage_trends(
    coverage: dict, history: list[dict], threshold_drop: float = 5.0
) -> list[dict]:
    """Check for coverage regression trends.

    Returns list of alerts if coverage dropped significantly.
    """
    alerts = []
    if not history:
        return alerts

    current_pct = coverage.get("statements", {}).get("pct", 0)
    if current_pct == 0:
        return alerts

    last = history[-1]
    last_pct = last.get("statements", {}).get("pct", 0)
    if last_pct > 0:
        drop = last_pct - current_pct
        if drop >= threshold_drop:
            alerts.append(
                {
                    "severity": "critical",
                    "metric": "Coverage Regression",
                    "value": f"{current_pct}% (dropped {drop:.1f}% from {last_pct}%)",
                    "threshold": f"drop < {threshold_drop}%",
                    "message": f"Cobertura de statements caiu {drop:.1f}% desde a última execução.",
                    "action": "Investigar alterações recentes que removeram testes ou adicionaram código não testado.",
                }
            )
        elif drop > 0:
            alerts.append(
                {
                    "severity": "warning",
                    "metric": "Coverage Slight Drop",
                    "value": f"{current_pct}% (dropped {drop:.1f}%)",
                    "threshold": f"drop < {threshold_drop}%",
                    "message": f"Cobertura caiu levemente ({drop:.1f}%). Monitorar tendência.",
                    "action": "Adicionar testes para novo código nas próximas PRPs.",
                }
            )

    zero_files = coverage.get("zero_coverage_files", [])
    if zero_files:
        alerts.append(
            {
                "severity": "critical",
                "metric": "Zero Coverage Files",
                "value": f"{len(zero_files)} arquivo(s)",
                "threshold": "0 arquivos com 0% cobertura",
                "message": f"{len(zero_files)} arquivo(s) de implementação sem nenhum teste.",
                "action": "Adicionar testes para: "
                + ", ".join(zero_files[:5])
                + ("..." if len(zero_files) > 5 else ""),
            }
        )

    return alerts


def check_coverage_thresholds(coverage: dict, thresholds: dict) -> list[dict]:
    """Check coverage against configured thresholds."""
    alerts = []

    stmt = coverage.get("statements", {})
    branch = coverage.get("branches", {})
    func = coverage.get("functions", {})
    lines = coverage.get("lines", {})

    stmt_pct = stmt.get("pct", 0)
    stmt_threshold = thresholds.get("statements", 80)
    if stmt_pct < stmt_threshold:
        alerts.append(
            {
                "severity": "critical",
                "metric": "Statements Coverage",
                "value": f"{stmt_pct}%",
                "threshold": f">= {stmt_threshold}%",
                "message": f"Cobertura de statements ({stmt_pct}%) abaixo do threshold ({stmt_threshold}%).",
                "action": "Adicionar testes unitários para aumentar cobertura.",
            }
        )

    branch_pct = branch.get("pct", 0)
    branch_threshold = thresholds.get("branches", 70)
    if branch_pct > 0 and branch_pct < branch_threshold:
        alerts.append(
            {
                "severity": "high",
                "metric": "Branches Coverage",
                "value": f"{branch_pct}%",
                "threshold": f">= {branch_threshold}%",
                "message": f"Cobertura de branches ({branch_pct}%) abaixo do threshold ({branch_threshold}%).",
                "action": "Adicionar testes para caminhos condicionais não cobertos.",
            }
        )

    func_pct = func.get("pct", 0)
    func_threshold = thresholds.get("functions", 80)
    if func_pct > 0 and func_pct < func_threshold:
        alerts.append(
            {
                "severity": "high",
                "metric": "Functions Coverage",
                "value": f"{func_pct}%",
                "threshold": f">= {func_threshold}%",
                "message": f"Cobertura de funções ({func_pct}%) abaixo do threshold ({func_threshold}%).",
                "action": "Adicionar testes para funções não cobertas.",
            }
        )

    lines_pct = lines.get("pct", 0)
    lines_threshold = thresholds.get("lines", 80)
    if lines_pct > 0 and lines_pct < lines_threshold:
        alerts.append(
            {
                "severity": "high",
                "metric": "Lines Coverage",
                "value": f"{lines_pct}%",
                "threshold": f">= {lines_threshold}%",
                "message": f"Cobertura de linhas ({lines_pct}%) abaixo do threshold ({lines_threshold}%).",
                "action": "Adicionar testes para linhas não cobertas.",
            }
        )

    return alerts
