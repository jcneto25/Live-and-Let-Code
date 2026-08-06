#!/usr/bin/env python3
"""observability.py — Observabilidade agentica consolidada (R2).

Gera um relatório consolidado do pipeline LLC a partir de artefatos já
existentes (`index.json`, `.ace/sessions/`, `docs/governance/`, worktrees git).

Saída:
  --json   → dump JSON com `sessions`, `worktrees`, `gates`, `govs`, `waves`
  (sem flag) → relatório textual de leitura humana ("OBSERVABILIDADE LLC")

Módulo first-party que estava AUSENTE (débito GOV-T2 / R2 — as 6 falhas
pré-existentes de test_observability.py). Implementado para satisfazer o
contrato do teste; read-only (nunca escreve em .ace/sessions/).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ── Caminhos (SESSIONS_DIR é normalizado p/ monkeypatch nos testes) ──
_ACE_DIR = Path(__file__).resolve().parents[1]
SESSIONS_DIR = _ACE_DIR / "sessions"
INDEX_FILE = _ACE_DIR / "index.json"
_GOV_DIR = Path(__file__).resolve().parents[2] / "docs" / "governance"
_WAVES_FILE = Path(__file__).resolve().parents[2] / "docs" / "planning" / "EXECUTION_WAVES.md"

_REJECTED = "rejected"


def _read_index_sessions() -> list[dict]:
    """Lê `.ace/index.json`. Retorna lista vazia se ausente/corrompido (degradação)."""
    if not INDEX_FILE.exists():
        return []
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8")).get("sessions", [])
    except (json.JSONDecodeError, OSError, AttributeError):
        return []


def _session_counts() -> dict:
    """Conta sessões por status (total == completed + in_progress + other)."""
    total = completed = in_progress = 0
    for s in _read_index_sessions():
        total += 1
        st = (s.get("status") or "").strip().lower()
        if st == "completed":
            completed += 1
        elif st == "in_progress":
            in_progress += 1
    other = total - completed - in_progress
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "other": other,
    }


def _worktrees_report() -> dict:
    """Conta e lista worktrees git (via `git worktree list --porcelain`)."""
    paths: list[str] = []
    try:
        r = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True, text=True, check=False,
        )
        if r.returncode == 0:
            for block in r.stdout.split("\n\n"):
                first = block.strip().splitlines()[0] if block.strip() else ""
                if first.startswith("worktree "):
                    paths.append(first[len("worktree "):])
    except (OSError, subprocess.SubprocessError):
        pass  # sem git → 0 worktrees (degradação graciosa)
    return {"count": len(paths), "list": paths}


def _gate_report() -> dict:
    """Varre as sessões por `<gate_result ... decision="rejected">` (gates falhos)."""
    failing: list[dict] = []
    if SESSIONS_DIR.exists():
        for f in sorted(SESSIONS_DIR.glob("*.md")):
            try:
                text = f.read_text(encoding="utf-8")
            except OSError:
                continue
            for m in re.finditer(r"<gate_result\b([^>]*)>", text):
                attrs = m.group(1)
                dm = re.search(r'decision="(\w+)"', attrs)
                if dm and dm.group(1) == _REJECTED:
                    failing.append({"file": f.name, "decision": _REJECTED})
    return {"failing": failing}


def _gov_report() -> dict:
    """Conta GOVs por Status (open/addressed/closed) em docs/governance/."""
    counts = {"open": 0, "addressed": 0, "closed": 0}
    if _GOV_DIR.exists():
        for f in sorted(_GOV_DIR.glob("GOV-*.md")):
            if f.name == "GOV-TEMPLATE.md":
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except OSError:
                continue
            m = re.search(r"\*\*Status\*\*:\s*(\w+)", text)
            if m and m.group(1).lower() in counts:
                counts[m.group(1).lower()] += 1
    return counts


def _waves_report() -> dict:
    """Presença do arquivo de ondas (planejamento de execução)."""
    return {"present": _WAVES_FILE.exists()}


def build_report() -> dict:
    """Constrói o relatório consolidado de observabilidade (read-only)."""
    return {
        "sessions": _session_counts(),
        "worktrees": _worktrees_report(),
        "gates": _gate_report(),
        "govs": _gov_report(),
        "waves": _waves_report(),
    }


def _format_text(rep: dict) -> str:
    s = rep["sessions"]
    w = rep["worktrees"]
    g = rep["govs"]
    failing = rep["gates"]["failing"]
    lines = [
        "═══ OBSERVABILIDADE LLC ═══",
        "",
        "SESSÕES:",
        f"  total: {s['total']}  ·  completed: {s['completed']}  ·  "
        f"in_progress: {s['in_progress']}  ·  other: {s['other']}",
        "",
        "WORKTREES:",
        f"  count: {w['count']}",
    ]
    for p in w["list"]:
        lines.append(f"    - {p}")
    lines += [
        "",
        f"GATES FALHOS (rejected): {len(failing)}",
        f"GOVs: open={g['open']} · addressed={g['addressed']} · closed={g['closed']}",
    ]
    for item in failing:
        lines.append(f"    - {item['file']} (gate rejected)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="observability.py",
        description="Observabilidade agêntica consolidada (R2) — read-only.",
    )
    parser.add_argument("--json", action="store_true", help="Saída em JSON")
    args = parser.parse_args(argv)

    rep = build_report()
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(_format_text(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
