#!/usr/bin/env python3
"""Testes para observability.py (R2 — observabilidade agentica consolidada).

Cobre o inventário exigido pelo artigo: sessões, worktrees, waves,
checkpoints/gates falhos, guardrails, reincidências por módulo.
"""

import json
import sys
from pathlib import Path

import pytest

OBS = Path(__file__).parent / "observability.py"


def run_obs(extra=()):
    return __import__("subprocess").run(
        [sys.executable, str(OBS)] + list(extra),
        capture_output=True, text=True,
    )


def test_exits_zero_with_json():
    r = run_obs(["--json"])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert "sessions" in data and "worktrees" in data


def test_sessions_counts():
    data = json.loads(run_obs(["--json"]).stdout)
    s = data["sessions"]
    assert s["total"] >= 1
    assert s["total"] == s["completed"] + s["in_progress"] + s["other"]


def test_worktrees_listed():
    data = json.loads(run_obs(["--json"]).stdout)
    assert "worktrees" in data
    assert isinstance(data["worktrees"]["count"], int)


def test_rejected_gates_detected(tmp_path, monkeypatch):
    """Sessão com gate_result rejected aparece em gates.failing."""
    d = tmp_path / ".ace" / "sessions"
    d.mkdir(parents=True)
    (d / "2026-01-01-001.md").write_text(
        '<gate_result step="10.6" decision="rejected">vuln crítica</gate_result>',
        encoding="utf-8")
    import observability
    monkeypatch.setattr(observability, "SESSIONS_DIR", d)
    rep = observability.build_report()
    assert any(g["file"] == "2026-01-01-001.md" for g in rep["gates"]["failing"])


def test_gov_block_summary():
    data = json.loads(run_obs(["--json"]).stdout)
    assert "govs" in data
    g = data["govs"]
    assert {"open", "addressed", "closed"} <= set(g)


def test_text_output_runs():
    r = run_obs()
    assert r.returncode == 0
    assert "SESSÕES" in r.stdout.upper() or "OBSERVABILIDADE" in r.stdout.upper()
