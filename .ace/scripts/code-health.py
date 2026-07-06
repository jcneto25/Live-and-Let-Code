#!/usr/bin/env python3
"""
Analisa a saúde estrutural do código via git history — foco em métricas de
Moved Code, Copy/Paste e refatoração, prevenindo degradação por agentes.

Uso:
    python .ace/scripts/code-health.py
    python .ace/scripts/code-health.py --since "30 days ago"
    python .ace/scripts/code-health.py --json
    python .ace/scripts/code-health.py --strict  # exit code 1 se thresholds violados
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def run_git_log(since: str) -> list[dict]:
    """Extrai log do git com --numstat para análise de churn."""
    cmd = [
        "git",
        "log",
        f"--since={since}",
        "--numstat",
        "--format=%H|%ai|%s",
        "--no-merges",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return []

    commits = []
    current = None
    for line in result.stdout.strip().split("\n"):
        if "|" in line and not line.startswith((" ", "\t")):
            if current:
                commits.append(current)
            parts = line.split("|", 2)
            current = {
                "hash": parts[0][:8],
                "date": parts[1][:10],
                "message": parts[2],
                "files": [],
            }
        elif current and line.strip():
            parts = line.split("\t")
            if len(parts) == 3:
                try:
                    added = int(parts[0]) if parts[0] != "-" else 0
                    deleted = int(parts[1]) if parts[1] != "-" else 0
                except ValueError:
                    added = deleted = 0
                current["files"].append(
                    {"path": parts[2], "added": added, "deleted": deleted}
                )
    if current:
        commits.append(current)
    return commits


def classify_changes(commits: list[dict]) -> dict:
    """Classifica alterações em Added, Deleted, Modified, Moved, Copy/Pasted."""
    stats = {
        "added": 0,
        "deleted": 0,
        "modified": 0,
        "moved_min": 0,
        "moved_est": 0,
        "copy_est": 0,
    }
    new_files = set()
    modified_files = set()

    for c in commits:
        for f in c["files"]:
            path = f["path"]
            if "=>" in path and "{" in path:
                stats["moved_min"] += f["added"] + f["deleted"]
                new_files.add(path.split("=>")[-1].strip().rstrip("}").strip())
            elif f["added"] > 0 and f["deleted"] == 0:
                if path not in modified_files:
                    stats["added"] += f["added"]
                    new_files.add(path)
            elif f["deleted"] > 0 and f["added"] == 0:
                stats["deleted"] += f["deleted"]
            else:
                stats["modified"] += f["added"] + f["deleted"]
                modified_files.add(path)

    est_new = stats["added"] + stats["moved_min"]
    est_all = est_new + stats["modified"] + stats["deleted"]

    if est_all > 0:
        stats["pct_moved"] = round((stats["moved_min"] / est_all) * 100, 1)
        stats["pct_added"] = round((stats["added"] / est_all) * 100, 1)
        stats["pct_modified"] = round((stats["modified"] / est_all) * 100, 1)
    else:
        stats["pct_moved"] = stats["pct_added"] = stats["pct_modified"] = 0

    copy_count = 0
    if len(commits) >= 10:
        for i, c1 in enumerate(commits[:-1]):
            for c2 in commits[i + 1 : i + 5]:
                f1 = set(f["path"] for f in c1["files"] if f["added"] > 30)
                f2 = set(f["path"] for f in c2["files"] if f["added"] > 30)
                for p1 in f1:
                    for p2 in f2:
                        if p1 != p2 and Path(p1).stem == Path(p2).stem:
                            copy_count += 1
    stats["copy_est"] = copy_count

    return stats


def analyze_file_age(commits: list[dict]) -> dict:
    """Analisa idade dos arquivos modificados."""
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    total_mod = 0
    old_mod = 0

    for c in commits:
        for f in c["files"]:
            total_mod += f["added"] + f["deleted"]
            if c["date"] < cutoff:
                old_mod += f["added"] + f["deleted"]

    return {
        "total_lines_modified": total_mod,
        "lines_in_files_older_than_30d": old_mod,
        "pct_legacy_touched": round((old_mod / total_mod * 100), 1)
        if total_mod > 0
        else 0,
    }


# ── Coverage Tracking ─────────────────────────────────────────────


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

            # vitest/jest format: { "path/to/file.ts": { "s": {...}, "f": {...}, "b": {...} } }
            if isinstance(data, dict) and all(
                isinstance(v, dict) and "s" in v for v in data.values()
            ):
                return _parse_vitest_coverage(data)

            # pytest-cov format: { "files": { "path": { "summary": {...} } } }
            if isinstance(data, dict) and "files" in data:
                return _parse_pytest_coverage(data)

            # generic JSON with totals
            if isinstance(data, dict) and "total" in data:
                return _parse_generic_coverage(data)

        elif suffix in (".out", ".cov"):
            # go test -coverprofile
            return _parse_go_coverage(coverage_file)

        elif suffix in (".info", ".lcov"):
            # lcov format
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

        # statements
        s = file_data.get("s", {})
        for _, count in s.items():
            total_statements += 1
            if count > 0:
                covered_statements += 1

        # branches
        b = file_data.get("b", {})
        for _, branches in b.items():
            for _, count in branches.items():
                total_branches += 1
                if count > 0:
                    covered_branches += 1

        # functions
        f = file_data.get("f", {})
        for _, count in f.items():
            total_functions += 1
            if count > 0:
                covered_functions += 1

        # lines (approximate from statements)
        file_lines = len(s)
        file_covered = sum(1 for c in s.values() if c > 0)
        total_lines += file_lines
        covered_lines += file_covered

        # per-file stats
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
    # Keep only last max_entries
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

    # Compare with last entry
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

    # Check for zero-coverage files
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

    # Statements threshold
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

    # Branches threshold
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

    # Functions threshold
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

    # Lines threshold
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


# ── Threshold Checks ──────────────────────────────────────────────


def check_thresholds(
    stats: dict,
    age: dict,
    coverage: dict | None = None,
    coverage_thresholds: dict | None = None,
    coverage_history: list[dict] | None = None,
) -> list[dict]:
    """Verifica thresholds e gera alertas."""
    alerts = []

    if stats.get("pct_moved", 0) < 10:
        alerts.append(
            {
                "severity": "critical",
                "metric": "Moved Code %",
                "value": f"{stats['pct_moved']}%",
                "threshold": "≥ 10%",
                "message": "Perda estrutural de manutenibilidade. Código não está sendo reorganizado em módulos.",
                "action": "Identificar blocos duplicados e propor refatoração cross-PRP.",
            }
        )

    if stats.get("copy_est", 0) > stats.get("moved_min", 0):
        alerts.append(
            {
                "severity": "high",
                "metric": "Copy/Paste vs Moved",
                "value": f"copy={stats['copy_est']} moved={stats['moved_min']}",
                "threshold": "copy ≤ moved",
                "message": "Duplicação superando reuso. Princípio DRY em risco.",
                "action": "Revisar PRPs recentes: consolidar código duplicado em módulo compartilhado.",
            }
        )

    if age.get("pct_legacy_touched", 30) < 20:
        alerts.append(
            {
                "severity": "high",
                "metric": "Legacy Code Touch %",
                "value": f"{age['pct_legacy_touched']}%",
                "threshold": "≥ 20%",
                "message": "Código antigo (>30 dias) não está sendo refatorado. Agentes focam apenas em novas linhas.",
                "action": "Agendar onda de refatoração de código legacy nos próximos PRPs.",
            }
        )

    # Coverage checks
    if coverage:
        if coverage_thresholds:
            alerts.extend(check_coverage_thresholds(coverage, coverage_thresholds))
        if coverage_history:
            alerts.extend(check_coverage_trends(coverage, coverage_history))

    if not alerts:
        alerts.append(
            {
                "severity": "ok",
                "metric": "Code Health",
                "value": "Todos os thresholds OK",
                "threshold": "—",
                "message": "Saúde estrutural do código dentro dos parâmetros.",
                "action": "Manter monitoramento nas próximas ondas.",
            }
        )

    return alerts


def main():
    parser = argparse.ArgumentParser(
        description="Analisa saúde estrutural do código via git history"
    )
    parser.add_argument(
        "--since", type=str, default="90 days ago", help="Período de análise"
    )
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    parser.add_argument(
        "--strict", action="store_true", help="Exit code 1 se thresholds violados"
    )
    parser.add_argument(
        "--coverage-file",
        type=str,
        help="Caminho do arquivo de cobertura (ex: coverage/coverage-final.json)",
    )
    parser.add_argument(
        "--coverage-history",
        type=str,
        default=".ace/coverage-history.json",
        help="Arquivo para armazenar histórico de cobertura",
    )
    parser.add_argument(
        "--coverage-threshold-statements",
        type=int,
        default=80,
        help="Threshold minimo de statements coverage (%%)",
    )
    parser.add_argument(
        "--coverage-threshold-branches",
        type=int,
        default=70,
        help="Threshold minimo de branches coverage (%%)",
    )
    parser.add_argument(
        "--coverage-threshold-functions",
        type=int,
        default=80,
        help="Threshold minimo de functions coverage (%%)",
    )
    parser.add_argument(
        "--coverage-threshold-lines",
        type=int,
        default=80,
        help="Threshold minimo de lines coverage (%%)",
    )
    parser.add_argument(
        "--coverage-regression-threshold",
        type=float,
        default=5.0,
        help="Threshold de queda de cobertura para alerta critico (%%)",
    )
    args = parser.parse_args()

    commits = run_git_log(args.since)
    if not commits:
        result = {
            "commits_analyzed": 0,
            "period": args.since,
            "alerts": [
                {
                    "severity": "ok",
                    "metric": "Code Health",
                    "value": "sem commits",
                    "threshold": "—",
                    "message": "Nenhum commit no período analisado.",
                    "action": "—",
                }
            ],
        }
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("✅ Nenhum commit no período.")
        return 0

    stats = classify_changes(commits)
    age = analyze_file_age(commits)

    # Parse coverage report if provided
    coverage = None
    coverage_history = []
    trend_alerts = []
    if args.coverage_file:
        coverage = parse_coverage_report(Path(args.coverage_file))
        if coverage:
            # Load history
            coverage_history = load_coverage_history(Path(args.coverage_history))
            # Check trends BEFORE saving current to history
            if coverage_history:
                trend_alerts = check_coverage_trends(
                    coverage, coverage_history, args.coverage_regression_threshold
                )
            # Save current to history
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "statements": coverage.get("statements", {}),
                "branches": coverage.get("branches", {}),
                "functions": coverage.get("functions", {}),
                "lines": coverage.get("lines", {}),
            }
            coverage_history.append(history_entry)
            save_coverage_history(Path(args.coverage_history), coverage_history)

    coverage_thresholds = {
        "statements": args.coverage_threshold_statements,
        "branches": args.coverage_threshold_branches,
        "functions": args.coverage_threshold_functions,
        "lines": args.coverage_threshold_lines,
    }

    alerts = check_thresholds(
        stats, age, coverage, coverage_thresholds, coverage_history
    )
    # Add trend alerts
    alerts.extend(trend_alerts)

    result = {
        "commits_analyzed": len(commits),
        "period": args.since,
        "stats": stats,
        "file_age": age,
        "alerts": alerts,
    }
    if coverage:
        result["coverage"] = coverage

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'=' * 60}")
        print(f"📊 SAÚDE ESTRUTURAL DO CÓDIGO")
        print(f"{'=' * 60}")
        print(f"Período: {args.since}")
        print(f"Commits analisados: {len(commits)}")
        print(f"\n📈 Distribuição de alterações:")
        print(f"   Added:       {stats['added']:>8} linhas ({stats['pct_added']}%)")
        print(
            f"   Modified:    {stats['modified']:>8} linhas ({stats['pct_modified']}%)"
        )
        print(f"   Moved (min): {stats['moved_min']:>8} linhas ({stats['pct_moved']}%)")
        print(f"   Deleted:     {stats['deleted']:>8} linhas")
        print(f"\n📋 Idade do código modificado:")
        print(f"   Total modificado: {age['total_lines_modified']} linhas")
        print(
            f"   Em arquivos >30d: {age['lines_in_files_older_than_30d']} linhas ({age['pct_legacy_touched']}%)"
        )

        if coverage:
            stmt = coverage.get("statements", {})
            branch = coverage.get("branches", {})
            func = coverage.get("functions", {})
            lines_cov = coverage.get("lines", {})
            print(f"\n📊 Cobertura de Testes:")
            print(
                f"   Statements: {stmt.get('pct', 0)}% ({stmt.get('covered', 0)}/{stmt.get('total', 0)})"
            )
            if branch.get("total", 0) > 0:
                print(
                    f"   Branches:   {branch.get('pct', 0)}% ({branch.get('covered', 0)}/{branch.get('total', 0)})"
                )
            if func.get("total", 0) > 0:
                print(
                    f"   Functions:  {func.get('pct', 0)}% ({func.get('covered', 0)}/{func.get('total', 0)})"
                )
            if lines_cov.get("total", 0) > 0:
                print(
                    f"   Lines:      {lines_cov.get('pct', 0)}% ({lines_cov.get('covered', 0)}/{lines_cov.get('total', 0)})"
                )
            zero_files = coverage.get("zero_coverage_files", [])
            if zero_files:
                print(f"   ⚠️  Zero coverage files: {len(zero_files)}")

        print(f"\n⚠️  Alertas:")

        has_critical = False
        for a in alerts:
            icon = {"critical": "🔴", "high": "🟡", "warning": "🟠", "ok": "✅"}.get(
                a["severity"], "⚪"
            )
            if a["severity"] == "critical":
                has_critical = True
            print(f"   {icon} [{a['severity'].upper()}] {a['metric']}: {a['message']}")
            if a["severity"] != "ok":
                print(f"      → Ação recomendada: {a['action']}")

        print(f"{'=' * 60}")

    if args.strict:
        return 1 if any(a["severity"] == "critical" for a in alerts) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
