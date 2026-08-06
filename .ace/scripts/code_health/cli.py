#!/usr/bin/env python3
"""code-health — CLI + orquestração com fitness functions."""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .gitlog import analyze_file_age, classify_changes, run_git_log
from .coverage import (
    load_coverage_history,
    parse_coverage_report,
    save_coverage_history,
)
from .thresholds import check_thresholds
from .gitlog import SCRIPTS_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Analisa saúde estrutural do código via git history"
    )
    parser.add_argument(
        "--since", type=str, default="90 days ago", help="Período de análise"
    )
    parser.add_argument(
        "--fitness",
        action="store_true",
        help="Inclui verificacao de fitness functions (conformidade arquitetural)",
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

    coverage = None
    coverage_history = []
    trend_alerts = []
    if args.coverage_file:
        coverage = parse_coverage_report(Path(args.coverage_file))
        if coverage:
            coverage_history = load_coverage_history(Path(args.coverage_history))
            if coverage_history:
                trend_alerts = check_coverage_trends(
                    coverage, coverage_history, args.coverage_regression_threshold
                )
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
    alerts.extend(trend_alerts)

    fitness_result = None
    eval_summary = None
    try:
        from llc_evals.report import build_eval_summary

        root = Path.cwd()
        bdir = root / ".ace" / "evals" / "baselines"
        rdir = root / ".ace" / "evals" / "results"
        if bdir.exists() or rdir.exists():
            eval_summary = build_eval_summary(
                baselines_dir=bdir, results_dir=rdir,
            )
    except Exception as e:  # noqa: BLE001 — seção eval é best-effort
        alerts.append({
            "severity": "warning",
            "metric": "Eval Summary",
            "value": "erro",
            "threshold": "—",
            "message": f"Nao foi possivel gerar o resumo de evals: {e}",
            "action": "Verificar se llc_evals esta instalado e .ace/evals/ existe.",
        })

    if args.fitness:
        try:
            fitness_script = SCRIPTS_DIR / "fitness-functions.py"
            if fitness_script.exists():
                proc = subprocess.run(
                    [sys.executable, str(fitness_script), "--all", "--json"],
                    capture_output=True, text=True, cwd=Path.cwd(),
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    fitness_data = json.loads(proc.stdout)
                    fitness_result = fitness_data
                    for name, check in fitness_data.get("results", {}).items():
                        if check.get("blocked"):
                            alerts.append({
                                "severity": "critical",
                                "metric": f"Fitness: {check['label']}",
                                "value": f"{check['violations_count']} violacao(oes)",
                                "threshold": "0",
                                "message": check.get("description", ""),
                                "action": "Corrigir violacoes em core modules antes do merge. Use fitness-functions.py para detalhes.",
                            })
                        elif not check.get("passed") and check.get("passed") is not None:
                            alerts.append({
                                "severity": "high",
                                "metric": f"Fitness: {check['label']}",
                                "value": f"{check['violations_count']} alerta(s)",
                                "threshold": "0",
                                "message": check.get("description", ""),
                                "action": "Registrar em divida tecnica. Revisar na proxima iteracao.",
                            })
        except Exception as e:
            alerts.append({
                "severity": "warning",
                "metric": "Fitness Functions",
                "value": "erro",
                "threshold": "—",
                "message": f"Nao foi possivel executar fitness functions: {e}",
                "action": "Verificar se PyYAML esta instalado e .ace/arch-config.yaml existe.",
            })

    result = {
        "commits_analyzed": len(commits),
        "period": args.since,
        "stats": stats,
        "file_age": age,
        "alerts": alerts,
    }
    if coverage:
        result["coverage"] = coverage
    if fitness_result:
        result["fitness"] = fitness_result
    if eval_summary and eval_summary.get("steps_analyzed"):
        result["eval_summary"] = eval_summary

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

        if fitness_result:
            print(f"\n🏗️  Fitness Functions (Conformidade Arquitetural):")
            for name, check in fitness_result.get("results", {}).items():
                icon = "✅" if check.get("passed") else ("🔴" if check.get("blocked") else "🟡")
                if check.get("passed") is None:
                    icon = "⚠️"
                print(f"   {icon} {check['label']}: ", end="")
                if check.get("violations_count", 0) > 0:
                    print(f"{check['violations_count']} violacao(oes)")
                    for v in check.get("violations", []):
                        sev = v.get("severity", "warn")
                        print(f"      {'🔴' if sev == 'block' else '🟡'} {v.get('module', v.get('detail', ''))}")
                else:
                    print("OK")

        if eval_summary and eval_summary.get("steps_analyzed"):
            print(f"\n📊 Eval Summary (Pareto custo×qualidade):")
            print(f"   Steps analisados: {eval_summary['steps_analyzed']}")
            w = eval_summary.get("worst_efficiency")
            if w:
                print(
                    f"   🔻 Pior eficiência: step {w['step']} "
                    f"(eff {w['efficiency_score']:g}, fase {w['phase']})"
                )
            r = eval_summary.get("highest_rework_waste")
            if r:
                print(
                    f"   🔻 Maior rework: step {r['step']} "
                    f"({r['rework_waste'] * 100:.0f}% tokens em retries)"
                )

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
