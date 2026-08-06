"""Testes para llc_evals.report — Dashboard Pareto (PRP-EVALS-F5).

RF-EF5.1: rank_by_efficiency() — steps por EfficiencyScore crescente (pior→melhor).
RF-EF5.2: rank_by_rework_waste() — steps por ReworkWaste decrescente (maior→menor).
RF-EF5.3: generate_report() cria .ace/evals/results/report-{date}.md; `llc eval report` ponta-a-ponta.
RF-EF5.4: build_eval_summary() alimenta a seção "Eval Summary" do code-health.
"""
from datetime import date

import pytest
import yaml

from llc_evals import aggregate, report


# ── RF-EF5.1: ranking por EfficiencyScore (menor = pior) ─────────────────────
def test_rank_by_efficiency_ascending():
    """RF-EF5.1: 5 steps com scores distintos → ordem crescente (pior→melhor)."""
    steps = [
        {"step": "11", "quality_score": 78, "token_cost": 48000,
         "efficiency_score": 14.1, "phase": "warmup"},
        {"step": "5", "quality_score": 86, "token_cost": 15500,
         "efficiency_score": 20.1, "phase": "stable"},
        {"step": "1", "quality_score": 92, "token_cost": 30000,
         "efficiency_score": 18.5, "phase": "collecting"},
        {"step": "3", "quality_score": 60, "token_cost": 12000,
         "efficiency_score": 12.0, "phase": "stable"},
        {"step": "8", "quality_score": 90, "token_cost": 9000,
         "efficiency_score": 22.5, "phase": "stable"},
    ]
    ranked = report.rank_by_efficiency(steps)
    scores = [s["efficiency_score"] for s in ranked]
    assert scores == sorted(scores)  # crescente
    assert ranked[0]["step"] == "3"   # pior custo-benefício primeiro
    assert ranked[-1]["step"] == "8"  # melhor por último


def test_rank_by_efficiency_empty():
    assert report.rank_by_efficiency([]) == []


# ── RF-EF5.2: ranking por ReworkWaste (maior = pior) ─────────────────────────
def test_rank_by_rework_waste_descending():
    """RF-EF5.2: steps com retries → ordem decrescente de desperdício."""
    steps = [
        {"step": "3", "rework_waste": 0.34, "retries": 2},
        {"step": "5", "rework_waste": 0.10, "retries": 1},
        {"step": "11", "rework_waste": 0.25, "retries": 3},
    ]
    ranked = report.rank_by_rework_waste(steps)
    wastes = [s["rework_waste"] for s in ranked]
    assert wastes == sorted(wastes, reverse=True)  # decrescente
    assert ranked[0]["step"] == "3"   # maior desperdício primeiro
    assert ranked[-1]["step"] == "5"


def test_rank_by_rework_waste_empty():
    assert report.rank_by_rework_waste([]) == []


# ── RF-EF5.3: generate_report() cria report-{date}.md ───────────────────────
def test_generate_report_creates_markdown(tmp_path):
    """RF-EF5.3: gera .ace/evals/results/report-{date}.md válido."""
    baselines_dir, results_dir = _seed_data(tmp_path)
    out_dir = tmp_path / ".ace" / "evals" / "results"
    path = report.generate_report(
        baselines_dir=baselines_dir,
        results_dir=results_dir,
        output_dir=out_dir,
        report_date="2026-08-06",
    )
    assert path.exists()
    assert path.name == "report-2026-08-06.md"
    text = path.read_text(encoding="utf-8")
    assert "# Eval Report" in text
    assert "Pareto: Eficiência" in text
    assert "Pareto: Desperdício" in text
    # steps presentes nas tabelas
    assert "11" in text and "5" in text
    assert "warmup" in text and "stable" in text


def test_generate_report_default_date(tmp_path):
    """Sem data explícita → date.today()."""
    baselines_dir, results_dir = _seed_data(tmp_path)
    path = report.generate_report(
        baselines_dir=baselines_dir, results_dir=results_dir,
        output_dir=tmp_path / "out",
    )
    assert path.name == f"report-{date.today()}.md"


# ── RF-EF5.3 end-to-end: `llc eval report` via Click ────────────────────────
def test_eval_report_cli_creates_file(tmp_path, monkeypatch):
    """RF-EF5.3 ponta-a-ponta: `llc eval report` → Markdown criado, rc 0.

    Cobre a fiação Click (grupo eval + subcomando) — o contrato que o PRP
    especifica, não apenas generate_report() unitário.
    """
    from click.testing import CliRunner

    from llc.cli import cli

    monkeypatch.chdir(tmp_path)
    _seed_data(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["eval", "report", "--output", str(tmp_path / "out")],
    )
    assert result.exit_code == 0
    assert (tmp_path / "out" / f"report-{date.today()}.md").exists()


def test_eval_report_cli_with_json_flag(tmp_path, monkeypatch):
    """`llc eval report --json` exibe o summary em JSON (sem quebrar)."""
    from click.testing import CliRunner

    from llc.cli import cli

    monkeypatch.chdir(tmp_path)
    _seed_data(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["eval", "report", "--output", str(tmp_path / "out"), "--json"],
    )
    assert result.exit_code == 0
    assert "worst_efficiency" in result.output


# ── RF-EF5.4: build_eval_summary() para o code-health ────────────────────────
def test_build_eval_summary_returns_data(tmp_path):
    """RF-EF5.4: resumo com ranking e topo de ineficiência."""
    baselines_dir, results_dir = _seed_data(tmp_path)
    summary = report.build_eval_summary(
        baselines_dir=baselines_dir, results_dir=results_dir,
    )
    assert "worst_efficiency" in summary
    assert "highest_rework_waste" in summary
    assert "steps_analyzed" in summary
    assert summary["steps_analyzed"] >= 2
    # o pior em eficiência e o pior em rework são identificados
    assert summary["worst_efficiency"]["step"] == "11"
    assert summary["highest_rework_waste"]["step"] == "5"


def test_build_eval_summary_empty_dirs(tmp_path):
    """Sem dados → resumo vazio sem exceção."""
    empty = tmp_path / "baselines"
    empty.mkdir(parents=True)
    summary = report.build_eval_summary(
        baselines_dir=empty, results_dir=tmp_path / "results",
    )
    assert summary["steps_analyzed"] == 0
    assert summary["worst_efficiency"] is None
    assert summary["highest_rework_waste"] is None


# ── Edge cases (review): fallback filename, zero-run skip, YAML malformado ──
def test_load_rework_rows_filename_fallback(tmp_path):
    """Sem step_id no YAML → fallback do filename; id pontuado (11.1) sobrevive."""
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True)
    (results_dir / "step-11.1-2026-08-06.yaml").write_text(
        "rework_waste: 0.20\nretries: 2\n", encoding="utf-8"
    )
    rows = report.load_rework_rows(results_dir)
    assert len(rows) == 1
    assert rows[0]["step"] == "11.1"
    assert rows[0]["rework_waste"] == pytest.approx(0.20)


def test_load_rework_rows_skips_malformed_yaml(tmp_path):
    """Arquivo corrompido → skip sem exceção."""
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True)
    (results_dir / "step-3-2026-08-06.yaml").write_text(
        "rework_waste: [broken\n", encoding="utf-8"
    )
    rows = report.load_rework_rows(results_dir)
    assert rows == []


def test_load_efficiency_rows_skips_zero_run_bucket(tmp_path):
    """Baseline sem runs (bucket vazio) → fora do ranking."""
    baselines_dir = tmp_path / "baselines"
    manager = aggregate.BaselineManager(baselines_dir)
    # cria arquivo de baseline com bucket zerado
    manager.record_run(step_id="1", quality_score=90.0, token_cost=10000.0,
                       source="level_3")
    baseline = manager._empty("2")
    (baselines_dir / "step-2.yaml").write_text(
        yaml.safe_dump(baseline), encoding="utf-8"
    )
    rows = report.load_efficiency_rows(baselines_dir)
    steps = [r["step"] for r in rows]
    assert "2" not in steps
    assert "1" in steps


def test_load_efficiency_rows_skips_malformed_baseline(tmp_path):
    """Baseline YAML corrompida → skip sem exceção (paridade com rework)."""
    baselines_dir = tmp_path / "baselines"
    baselines_dir.mkdir(parents=True)
    (baselines_dir / "step-9.yaml").write_text(
        "active_precision: [broken\n", encoding="utf-8"
    )
    rows = report.load_efficiency_rows(baselines_dir)
    assert rows == []


# ── Helpers ──────────────────────────────────────────────────────────────────
def _seed_data(tmp_path):
    """Cria baselines (step-5, step-11) e results (step-5, step-11)."""
    baselines_dir = tmp_path / ".ace" / "evals" / "baselines"
    results_dir = tmp_path / ".ace" / "evals" / "results"
    manager = aggregate.BaselineManager(
        baselines_dir=baselines_dir, warmup_config={"n_min": 5, "n_stable": 10})
    # step-11: 7 runs warmup, eficiência baixa (78/48000)
    for _ in range(7):
        manager.record_run(step_id="11", quality_score=78.0,
                           token_cost=48000.0, source="level_3")
    # step-5: 12 runs stable, eficiência alta (86/15500)
    for _ in range(12):
        manager.record_run(step_id="5", quality_score=86.0,
                           token_cost=15500.0, source="level_3")

    aggregate.save_result(step_id="11", date="2026-08-06",
                          results_dir=results_dir,
                          result={"rework_waste": 0.10, "retries": 1})
    aggregate.save_result(step_id="5", date="2026-08-06",
                          results_dir=results_dir,
                          result={"rework_waste": 0.34, "retries": 2})
    return baselines_dir, results_dir
