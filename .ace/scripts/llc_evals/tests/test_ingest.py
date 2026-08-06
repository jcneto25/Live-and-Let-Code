"""Testes para llc_evals.ingest — conector sessão → BaselineManager (P1 pos-roadmap).

Cobre o elo que faltava: `<eval_metrics>` nas sessões ACE alimentam
`BaselineManager.record_run()` via `llc evals ingest`:
- parse_eval_metrics: extrai blocos XML das sessões
- quality_from_gate: quality score determinístico via <gate_result>
- ingest_sessions: grava baselines + idempotência (não duplica runs)
- CLI `llc evals ingest` ponta-a-ponta
"""
from datetime import date
from pathlib import Path

import pytest

from llc_evals.ingest import (
    ingest_sessions,
    parse_eval_metrics,
    quality_from_gate,
)

_SESSION_WITH_BLOCK = """---
session_id: "2026-08-06-023"
---

## Ações
<action_log>
<action type="file_modify"><file_delta>x.py</file_delta><description>ok</description></action>
</action_log>

## Gates
<gate_result step="10.9" decision="approved" reviewer="r">aprovado</gate_result>

<eval_metrics timestamp="2026-08-06T16:26:49">
  step: "10.9"
  tokens_in: 1416
  tokens_out: 471
  total_tokens: 1887
  cost_usd: 0.005661
  duration_s: 0
  retries: 0
  source: "level_3"
  precision: "estimated"
</eval_metrics>
"""

_SESSION_REJECTED = """<gate_result step="11" decision="rejected" reviewer="r">não</gate_result>

<eval_metrics timestamp="2026-08-06T10:00:00">
  step: "11"
  tokens_in: 100
  tokens_out: 50
  total_tokens: 150
  cost_usd: 0.000450
  duration_s: 0
  retries: 2
  source: "level_2"
  precision: "exact"
</eval_metrics>
"""


# ── parse_eval_metrics ───────────────────────────────────────────────────────
def test_parse_single_block():
    blocks = parse_eval_metrics(_SESSION_WITH_BLOCK)
    assert len(blocks) == 1
    b = blocks[0]
    assert b["step"] == "10.9"
    assert b["total_tokens"] == 1887
    assert b["source"] == "level_3"
    assert b["precision"] == "estimated"


def test_parse_multiple_blocks():
    content = _SESSION_WITH_BLOCK + "\n" + _SESSION_REJECTED
    blocks = parse_eval_metrics(content)
    assert len(blocks) == 2
    steps = {b["step"] for b in blocks}
    assert steps == {"10.9", "11"}


def test_parse_no_blocks():
    assert parse_eval_metrics("## Ações\nsem bloco") == []


def test_parse_ignores_placeholder_comment():
    content = "<!-- <eval_metrics ...> -->\n<eval_metrics timestamp=\"t\">\n  step: \"1\"\n  total_tokens: 10\n</eval_metrics>"
    blocks = parse_eval_metrics(content)
    assert len(blocks) == 1
    assert blocks[0]["step"] == "1"


# ── quality_from_gate ────────────────────────────────────────────────────────
def test_quality_approved_is_100():
    assert quality_from_gate(_SESSION_WITH_BLOCK) == 100.0


def test_quality_rejected_is_0():
    assert quality_from_gate(_SESSION_REJECTED) == 0.0


def test_quality_absent_is_none():
    assert quality_from_gate("## Ações\nsem gate") is None


# ── ingest_sessions ──────────────────────────────────────────────────────────
def _session_file(root: Path, session_id: str, content: str) -> Path:
    d = root / ".ace" / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{session_id}.md"
    path.write_text(content, encoding="utf-8")
    return path


def _setup(root: Path):
    """Root com 2 sessões (uma aprovada, uma rejeitada) + dirs evals."""
    _session_file(root, "2026-08-06-022", _SESSION_WITH_BLOCK)
    _session_file(root, "2026-08-06-023", _SESSION_REJECTED)
    (root / ".ace" / "evals" / "baselines").mkdir(parents=True, exist_ok=True)
    (root / ".ace" / "evals" / "results").mkdir(parents=True, exist_ok=True)
    return root


def test_ingest_creates_baselines(tmp_path):
    """P1: ingest alimenta record_run → baselines por step criados."""
    root = _setup(tmp_path)
    summary = ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
    )
    assert summary["runs_recorded"] == 2
    assert summary["errors"] == []
    assert (root / ".ace" / "evals" / "baselines" / "step-10.9.yaml").exists()
    assert (root / ".ace" / "evals" / "baselines" / "step-11.yaml").exists()


def test_ingest_is_idempotent(tmp_path):
    """P1: re-executar o ingest não duplica runs (baseline run_count estável)."""
    import yaml

    root = _setup(tmp_path)
    s1 = ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
    )
    assert s1["runs_recorded"] == 2
    s2 = ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
    )
    assert s2["runs_recorded"] == 0  # idempotente
    b = yaml.safe_load(
        (root / ".ace" / "evals" / "baselines" / "step-10.9.yaml").read_text()
    )
    assert b["run_count"] == 1


def test_ingest_dry_run_writes_nothing(tmp_path):
    """P1: --dry-run não grava baselines nem estado."""
    root = _setup(tmp_path)
    summary = ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
        dry_run=True,
    )
    assert summary["runs_recorded"] == 2
    assert not (root / ".ace" / "evals" / "baselines" / "step-10.9.yaml").exists()
    assert not (root / ".ace" / "evals" / "state.yaml").exists()


def test_ingest_records_quality_from_gate(tmp_path):
    """P1: quality_score do run vem do <gate_result> (100 aprovado / 0 rejeitado)."""
    import yaml

    root = _setup(tmp_path)
    ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
    )
    b = yaml.safe_load(
        (root / ".ace" / "evals" / "baselines" / "step-10.9.yaml").read_text()
    )
    l3 = b["by_precision_level"]["level_3"]
    assert l3["quality_score_avg"] == 100.0


def test_ingest_missing_sessions_dir_reports_error(tmp_path):
    """Sessions dir ausente → erro registrado, summary ainda retornado."""
    summary = ingest_sessions(
        sessions_dir=tmp_path / ".ace" / "sessions",
        baselines_dir=tmp_path / ".ace" / "evals" / "baselines",
    )
    assert summary["runs_recorded"] == 0
    assert len(summary["errors"]) == 1


def test_ingest_unknown_source_skipped(tmp_path):
    """Source desconhecido no bloco → erro, não grava baseline."""
    root = _setup(tmp_path)
    _session_file(root, "2026-08-06-024", """<eval_metrics timestamp="t">
  step: "7"
  total_tokens: 5
  source: "level_9"
</eval_metrics>""")
    summary = ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
    )
    assert summary["runs_recorded"] == 2  # só os blocos válidos
    assert len(summary["errors"]) == 1
    assert not (root / ".ace" / "evals" / "baselines" / "step-7.yaml").exists()


def test_ingest_default_quality_when_no_gate(tmp_path):
    """Sessão sem <gate_result> → quality default (80.0)."""
    import yaml

    root = _setup(tmp_path)
    _session_file(root, "2026-08-06-024", """<eval_metrics timestamp="t">
  step: "2"
  total_tokens: 100
  source: "level_3"
</eval_metrics>""")
    ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
        default_quality=80.0,
    )
    b = yaml.safe_load(
        (root / ".ace" / "evals" / "baselines" / "step-2.yaml").read_text()
    )
    assert b["by_precision_level"]["level_3"]["quality_score_avg"] == 80.0


# ── Regressões review ───────────────────────────────────────────────────────
def test_quality_ignores_commented_placeholder_gate():
    """Regressão review: placeholder comentado NÃO vira gate real (sem 100.0 falso)."""
    content = (
        "<!-- <gate_result step=\"10\" decision=\"approved\" reviewer=\"...\"> -->\n"
        "## Gates\n"
    )
    assert quality_from_gate(content) is None


def test_quality_real_gate_wins_over_placeholder():
    """Gate real aprovado ainda vale 100.0 mesmo com placeholder presente."""
    content = (
        "<!-- <gate_result step=\"10\" decision=\"approved\"> -->\n"
        '<gate_result step="10" decision="rejected" reviewer="r">real</gate_result>'
    )
    assert quality_from_gate(content) == 0.0


def test_ingest_skips_block_without_tokens(tmp_path):
    """Regressão review: bloco sem total_tokens não grava run lixo (0 tokens)."""
    root = _setup(tmp_path)
    _session_file(root, "2026-08-06-024", """<eval_metrics timestamp="t">
  step: "3"
  source: "level_3"
</eval_metrics>""")
    summary = ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
    )
    assert summary["runs_recorded"] == 2  # só os blocos com tokens
    assert len(summary["errors"]) == 1
    assert not (root / ".ace" / "evals" / "baselines" / "step-3.yaml").exists()


def test_idempotency_key_is_session_only(tmp_path):
    """Regressão review: chave = session_id (sessões imutáveis, 1 bloco/sessão)."""
    import yaml

    root = _setup(tmp_path)
    s1 = ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
    )
    assert s1["runs_recorded"] == 2
    state = yaml.safe_load((root / ".ace" / "evals" / "state.yaml").read_text())
    assert set(state["ingested"]) == {"2026-08-06-022", "2026-08-06-023"}
    # re-executa: nenhum run duplicado
    s2 = ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
    )
    assert s2["runs_recorded"] == 0


def test_ingest_migrates_legacy_state_keys(tmp_path):
    """Regressão review: estado legado 'session:timestamp' normalizado p/ session_id."""
    import yaml

    root = _setup(tmp_path)
    (root / ".ace" / "evals").mkdir(parents=True, exist_ok=True)
    (root / ".ace" / "evals" / "state.yaml").write_text(
        yaml.safe_dump({"ingested": ["2026-08-06-022:", "2026-08-06-023:"]}),
        encoding="utf-8",
    )
    s = ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
    )
    assert s["runs_recorded"] == 0  # já ingeridas (chaves migradas)


def test_ingest_skips_block_without_step(tmp_path):
    """P1: bloco sem step é ignorado (erro registrado, não quebra o ingest)."""
    root = _setup(tmp_path)
    _session_file(root, "2026-08-06-024", """<eval_metrics timestamp="t">
  tokens_in: 1
  total_tokens: 5
  source: "level_3"
</eval_metrics>""")
    summary = ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
    )
    assert summary["runs_recorded"] == 2  # só os 2 blocos válidos
    assert len(summary["errors"]) == 1


# ── CLI `llc evals ingest` ───────────────────────────────────────────────────
def test_cli_ingest_end_to_end(tmp_path, monkeypatch):
    """P1 ponta-a-ponta: `llc evals ingest` → baselines criados, rc 0."""
    from click.testing import CliRunner

    from llc.cli import cli

    root = _setup(tmp_path)
    monkeypatch.chdir(root)
    runner = CliRunner()
    result = runner.invoke(cli, ["eval", "ingest"])
    assert result.exit_code == 0
    assert "baseline" in result.output.lower() or "ingest" in result.output.lower()
    assert (root / ".ace" / "evals" / "baselines" / "step-10.9.yaml").exists()


def test_cli_ingest_dry_run_flag(tmp_path, monkeypatch):
    """`llc evals ingest --dry-run` não grava nada e ainda reporta runs."""
    from click.testing import CliRunner

    from llc.cli import cli

    root = _setup(tmp_path)
    monkeypatch.chdir(root)
    runner = CliRunner()
    result = runner.invoke(cli, ["eval", "ingest", "--dry-run"])
    assert result.exit_code == 0
    assert not (root / ".ace" / "evals" / "baselines" / "step-10.9.yaml").exists()
