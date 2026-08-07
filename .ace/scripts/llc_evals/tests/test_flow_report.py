"""Testes para llc_evals.flow_report — Relatório de Gargalos Reais (P4).

P4 pos-roadmap: cruza o caminho crítico do GraphEngine (ADR-0004 §2.7) com as
métricas de fluxo do Wizard (flow-metrics-*.yaml, PRP-WIZARD-1.2 RF-W1.2.3).

RF-P4.1: compute_bottlenecks() — step crítico com block_time > 0 (espera
        humana) ou rework (rework_count > 0 / first_pass false) é GARGALO
        ACIONÁVEL.
RF-P4.2: pacing — step crítico com maior cycle_time (o que determina a
        duração total hoje).
RF-P4.3: generate_flow_report() cria flow-report-{date}.md; `llc eval
        flow-report` ponta-a-ponta com ≥1 gargalo acionável por execução.
"""
from datetime import date

import pytest
import yaml

from llc_evals import flow_report


# ── RF-P4.1: compute_bottlenecks — gargalos acionáveis ──────────────────────
def test_bottleneck_espera_humana_when_block_time():
    """block_time > 0 → motivo 'espera_humana' (step aguardando gate/humano)."""
    metrics = {"by_step": {"10.9": {"cycle_time": 6, "block_time": 6,
                                    "first_pass": True}}}
    data = flow_report.compute_bottlenecks(["10.9"], metrics)
    assert data["bottlenecks"] == [{
        "step": "10.9", "reasons": ["espera_humana"],
        "block_time": 6, "rework_count": 0, "cycle_time": 6,
    }]


def test_bottleneck_retrabalho_when_rework_count():
    """rework_count > 0 → motivo 'retrabalho'."""
    metrics = {"by_step": {"3": {"cycle_time": 100, "block_time": 0,
                                 "rework_count": 2, "first_pass": False}}}
    data = flow_report.compute_bottlenecks(["3"], metrics)
    assert data["bottlenecks"][0]["reasons"] == ["retrabalho"]


def test_bottleneck_retrabalho_when_first_pass_false():
    """first_pass false (sem rework_count explícito) → 'retrabalho'."""
    metrics = {"by_step": {"5": {"cycle_time": 50, "block_time": 0,
                                 "first_pass": False}}}
    data = flow_report.compute_bottlenecks(["5"], metrics)
    assert data["bottlenecks"][0]["reasons"] == ["retrabalho"]


def test_bottleneck_no_reasons_excluded():
    """Step crítico com métricas mas sem espera/rework → fora dos gargalos."""
    metrics = {"by_step": {"8": {"cycle_time": 30, "block_time": 0,
                                 "first_pass": True}}}
    data = flow_report.compute_bottlenecks(["8"], metrics)
    assert data["bottlenecks"] == []
    assert data["with_metrics"] == 1  # mas conta nas métricas


def test_bottleneck_both_reasons():
    """block_time + rework juntos → dois motivos (mais acionável)."""
    metrics = {"by_step": {"11": {"cycle_time": 99, "block_time": 45,
                                  "rework_count": 1, "first_pass": False}}}
    data = flow_report.compute_bottlenecks(["11"], metrics)
    assert data["bottlenecks"][0]["reasons"] == ["espera_humana", "retrabalho"]


def test_bottleneck_sorted_by_reasons_then_block_time():
    """Ordenação: empate de motivos → maior block_time primeiro.

    Todos têm 1 motivo; o desempate por block_time decrescente põe quem
    espera há mais tempo (step 2, 60min) no topo.
    """
    metrics = {"by_step": {
        "1": {"cycle_time": 10, "block_time": 5, "first_pass": True},
        "2": {"cycle_time": 10, "block_time": 60, "first_pass": True},
        "3": {"cycle_time": 10, "block_time": 0, "rework_count": 1},
    }}
    data = flow_report.compute_bottlenecks(["1", "2", "3"], metrics)
    steps = [b["step"] for b in data["bottlenecks"]]
    assert steps == ["2", "1", "3"]


def test_without_metrics_gap():
    """Steps críticos sem dados de flow metrics → without_metrics (gap)."""
    metrics = {"by_step": {"3": {"cycle_time": 10, "block_time": 0}}}
    data = flow_report.compute_bottlenecks(
        ["3", "5", "10.9"], metrics)
    assert data["without_metrics"] == ["5", "10.9"]
    assert data["critical_total"] == 3
    assert data["with_metrics"] == 1


# ── RF-P4.2: pacing — maior cycle_time no caminho crítico ───────────────────
def test_pacing_is_max_cycle_time():
    """Pacing = step crítico com maior cycle_time (determina duração total)."""
    metrics = {"by_step": {
        "5.4": {"cycle_time": 15139, "block_time": 0, "first_pass": True},
        "3": {"cycle_time": 14915, "block_time": 0, "first_pass": True},
    }}
    data = flow_report.compute_bottlenecks(["3", "5.4"], metrics)
    assert data["pacing"] == {"step": "5.4", "cycle_time": 15139}


def test_pacing_none_when_no_data():
    """Sem nenhum step com dados → pacing None (sem exceção)."""
    data = flow_report.compute_bottlenecks(["3"], {"by_step": {}})
    assert data["pacing"] is None


# ── Edge cases ──────────────────────────────────────────────────────────────
def test_empty_inputs():
    """Lista vazia / dict vazio → resultado vazio sem exceção."""
    data = flow_report.compute_bottlenecks([], {})
    assert data == {
        "bottlenecks": [], "pacing": None, "critical_total": 0,
        "with_metrics": 0, "without_metrics": [],
    }


def test_non_dict_flow_metrics_graceful():
    """flow_metrics não-dict (corrompido) → degrada para sem métricas."""
    data = flow_report.compute_bottlenecks(["3"], "corrompido")
    assert data["bottlenecks"] == []
    assert data["with_metrics"] == 0
    assert data["without_metrics"] == ["3"]


def test_by_step_entry_non_dict_graceful():
    """Entrada de by_step não-dict → step tratado como sem dados."""
    metrics = {"by_step": {"3": "corrompido"}}
    data = flow_report.compute_bottlenecks(["3"], metrics)
    assert data["bottlenecks"] == []
    assert data["with_metrics"] == 0


def test_by_step_int_and_float_keys_normalized():
    """Fix review: chaves numéricas (arquivo sem aspas) → str(3) casa.

    Um flow-metrics-*.yaml escrito à mão com `3:` (sem aspas) carrega como
    int 3 e `10.9:` como float — sem a normalização, o step seria ignorado
    e cairia errado em without_metrics.
    """
    metrics = {"by_step": {
        3: {"cycle_time": 10, "block_time": 45, "first_pass": True},
        10.9: {"cycle_time": 6, "block_time": 0, "first_pass": True},
    }}
    data = flow_report.compute_bottlenecks(["3", "10.9"], metrics)
    assert data["bottlenecks"] == [{
        "step": "3", "reasons": ["espera_humana"],
        "block_time": 45, "rework_count": 0, "cycle_time": 10,
    }]
    assert data["with_metrics"] == 2
    assert data["without_metrics"] == []


# ── RF-P4.3: generate_flow_report() cria flow-report-{date}.md ──────────────
def _seed_flow_metrics(tmp_path, by_step=None):
    """Cria .ace/evals/results/flow-metrics-{date}.yaml de teste."""
    results_dir = tmp_path / ".ace" / "evals" / "results"
    results_dir.mkdir(parents=True)
    payload = {
        "metrics": {"cycle_time_avg_minutes": 9138,
                    "block_time_avg_minutes": 6,
                    "stale_rate_percent": 0,
                    "first_pass_rate_percent": 100},
        "by_step": by_step or {
            "10.9": {"cycle_time": 6, "block_time": 6, "first_pass": True},
            "3": {"cycle_time": 14915, "block_time": 0, "first_pass": True},
        },
        "generated_at": "2026-08-07T09:18:40",
        "baseline": True,
    }
    (results_dir / "flow-metrics-2026-08-07.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return results_dir


def test_generate_flow_report_creates_markdown(tmp_path):
    """RF-P4.3: gera flow-report-{date}.md com gargalos e pacing."""
    results_dir = _seed_flow_metrics(tmp_path)
    out_dir = tmp_path / "out"
    path = flow_report.generate_flow_report(
        project_root=tmp_path,
        results_dir=results_dir,
        output_dir=out_dir,
        report_date="2026-08-07",
    )
    assert path.exists()
    assert path.name == "flow-report-2026-08-07.md"
    text = path.read_text(encoding="utf-8")
    assert "# Flow Report" in text
    assert "Gargalos acionáveis" in text
    assert "Pacing atual" in text
    # gargalo real: step 10.9 com espera humana (block_time 6 > 0)
    assert "10.9" in text and "espera_humana" in text
    # pacing = maior cycle_time dos críticos com dados
    assert "14915" in text


def test_generate_flow_report_no_metrics_file(tmp_path):
    """Sem flow-metrics-*.yaml → relatório com gap, sem crash."""
    results_dir = tmp_path / ".ace" / "evals" / "results"
    results_dir.mkdir(parents=True)
    out_dir = tmp_path / "out"
    path = flow_report.generate_flow_report(
        project_root=tmp_path, results_dir=results_dir,
        output_dir=out_dir, report_date="2026-08-07",
    )
    text = path.read_text(encoding="utf-8")
    assert "Nenhum gargalo acionável" in text
    assert "gap" in text  # seção de steps críticos sem métricas
    assert "com métricas: 0" in text


def test_generate_flow_report_default_date(tmp_path):
    """Sem data explícita → date.today()."""
    results_dir = _seed_flow_metrics(tmp_path)
    path = flow_report.generate_flow_report(
        project_root=tmp_path, results_dir=results_dir,
        output_dir=tmp_path / "out",
    )
    assert path.name == f"flow-report-{date.today()}.md"


# ── RF-P4.3 end-to-end: `llc eval flow-report` via Click ────────────────────
def test_flow_report_cli_creates_file(tmp_path, monkeypatch):
    """`llc eval flow-report --project-root` → Markdown criado, rc 0."""
    from click.testing import CliRunner

    from llc.cli import cli

    monkeypatch.chdir(tmp_path)
    _seed_flow_metrics(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["eval", "flow-report", "--project-root", str(tmp_path),
              "--output", str(tmp_path / "out")],
    )
    assert result.exit_code == 0
    assert (tmp_path / "out" / f"flow-report-{date.today()}.md").exists()
    assert "Flow Report" in result.output
    assert "espera_humana" in result.output
