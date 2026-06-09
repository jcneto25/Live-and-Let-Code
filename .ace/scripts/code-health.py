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
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

def run_git_log(since: str) -> list[dict]:
    """Extrai log do git com --numstat para análise de churn."""
    cmd = ["git", "log", f"--since={since}", "--numstat", "--format=%H|%ai|%s", "--no-merges"]
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
            current = {"hash": parts[0][:8], "date": parts[1][:10], "message": parts[2], "files": []}
        elif current and line.strip():
            parts = line.split("\t")
            if len(parts) == 3:
                try:
                    added = int(parts[0]) if parts[0] != "-" else 0
                    deleted = int(parts[1]) if parts[1] != "-" else 0
                except ValueError:
                    added = deleted = 0
                current["files"].append({"path": parts[2], "added": added, "deleted": deleted})
    if current:
        commits.append(current)
    return commits


def classify_changes(commits: list[dict]) -> dict:
    """Classifica alterações em Added, Deleted, Modified, Moved, Copy/Pasted."""
    stats = {"added": 0, "deleted": 0, "modified": 0, "moved_min": 0, "moved_est": 0, "copy_est": 0}
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
            for c2 in commits[i+1:i+5]:
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
        "pct_legacy_touched": round((old_mod / total_mod * 100), 1) if total_mod > 0 else 0
    }


def check_thresholds(stats: dict, age: dict) -> list[dict]:
    """Verifica thresholds e gera alertas."""
    alerts = []

    if stats.get("pct_moved", 0) < 10:
        alerts.append({"severity": "critical",
                       "metric": "Moved Code %",
                       "value": f"{stats['pct_moved']}%",
                       "threshold": "≥ 10%",
                       "message": "Perda estrutural de manutenibilidade. Código não está sendo reorganizado em módulos.",
                       "action": "Identificar blocos duplicados e propor refatoração cross-PRP."})

    if stats.get("copy_est", 0) > stats.get("moved_min", 0):
        alerts.append({"severity": "high",
                       "metric": "Copy/Paste vs Moved",
                       "value": f"copy={stats['copy_est']} moved={stats['moved_min']}",
                       "threshold": "copy ≤ moved",
                       "message": "Duplicação superando reuso. Princípio DRY em risco.",
                       "action": "Revisar PRPs recentes: consolidar código duplicado em módulo compartilhado."})

    if age.get("pct_legacy_touched", 30) < 20:
        alerts.append({"severity": "high",
                       "metric": "Legacy Code Touch %",
                       "value": f"{age['pct_legacy_touched']}%",
                       "threshold": "≥ 20%",
                       "message": "Código antigo (>30 dias) não está sendo refatorado. Agentes focam apenas em novas linhas.",
                       "action": "Agendar onda de refatoração de código legacy nos próximos PRPs."})

    if not alerts:
        alerts.append({"severity": "ok",
                       "metric": "Code Health",
                       "value": "Todos os thresholds OK",
                       "threshold": "—",
                       "message": "Saúde estrutural do código dentro dos parâmetros.",
                       "action": "Manter monitoramento nas próximas ondas."})

    return alerts


def main():
    parser = argparse.ArgumentParser(description="Analisa saúde estrutural do código via git history")
    parser.add_argument("--since", type=str, default="90 days ago", help="Período de análise")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    parser.add_argument("--strict", action="store_true", help="Exit code 1 se thresholds violados")
    args = parser.parse_args()

    commits = run_git_log(args.since)
    if not commits:
        result = {"commits_analyzed": 0, "period": args.since, "alerts": [{"severity": "ok", "metric": "Code Health", "value": "sem commits", "threshold": "—", "message": "Nenhum commit no período analisado.", "action": "—"}]}
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("✅ Nenhum commit no período.")
        return 0

    stats = classify_changes(commits)
    age = analyze_file_age(commits)
    alerts = check_thresholds(stats, age)

    result = {
        "commits_analyzed": len(commits),
        "period": args.since,
        "stats": stats,
        "file_age": age,
        "alerts": alerts
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"📊 SAÚDE ESTRUTURAL DO CÓDIGO")
        print(f"{'='*60}")
        print(f"Período: {args.since}")
        print(f"Commits analisados: {len(commits)}")
        print(f"\n📈 Distribuição de alterações:")
        print(f"   Added:       {stats['added']:>8} linhas ({stats['pct_added']}%)")
        print(f"   Modified:    {stats['modified']:>8} linhas ({stats['pct_modified']}%)")
        print(f"   Moved (min): {stats['moved_min']:>8} linhas ({stats['pct_moved']}%)")
        print(f"   Deleted:     {stats['deleted']:>8} linhas")
        print(f"\n📋 Idade do código modificado:")
        print(f"   Total modificado: {age['total_lines_modified']} linhas")
        print(f"   Em arquivos >30d: {age['lines_in_files_older_than_30d']} linhas ({age['pct_legacy_touched']}%)")
        print(f"\n⚠️  Alertas:")

        has_critical = False
        for a in alerts:
            icon = {"critical": "🔴", "high": "🟡", "ok": "✅"}.get(a["severity"], "⚪")
            if a["severity"] == "critical":
                has_critical = True
            print(f"   {icon} [{a['severity'].upper()}] {a['metric']}: {a['message']}")
            if a["severity"] != "ok":
                print(f"      → Ação recomendada: {a['action']}")

        print(f"{'='*60}")

    if args.strict:
        return 1 if any(a["severity"] == "critical" for a in alerts) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
