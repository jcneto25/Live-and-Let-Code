"""Testes para llc_wizard.flow_metrics — PRP-WIZARD-1.2 (RF-W1.2.3/.4).

Cobertura:
- compute_flow_metrics: cycle time, block time, stale rate, first-pass rate
- export_flow_metrics: baseline na primeira execução, false nas seguintes
"""
from datetime import datetime, timedelta

import pytest

from llc_wizard.data import PipelineStatus, StepInfo, StepStatus
from llc_wizard.flow_metrics import (
    _minutes_between,
    compute_flow_metrics,
    export_flow_metrics,
)


def _fake_status(steps, since=None):
    """PipelineStatus com steps dados e mapa since (step_id → datetime)."""
    since = since or {}

    class Fake:
        def get_status(self):
            return PipelineStatus(steps=steps)

        def get_status_since(self, step_id):
            return since.get(step_id, datetime.now() - timedelta(minutes=10))

        def get_gate_for_step(self, step_id):
            return None

        def get_pending_hitl(self):
            return []

    return Fake()


def test_minutes_between_returns_positive():
    past = datetime.now() - timedelta(minutes=30)
    assert _minutes_between(past) == pytest.approx(30.0, abs=2)


def test_compute_cycle_time_and_block_time():
    """RF-W1.2.3: cycle time médio e block time (AWAITING_HUMAN)."""
    now = datetime.now()
    steps = [
        StepInfo(id="1", name="Visao", status=StepStatus.COMPLETED,
                 in_pipeline=True),
        StepInfo(id="2", name="Specs", status=StepStatus.IN_PROGRESS,
                 in_pipeline=True),
        StepInfo(id="3", name="PRDs", status=StepStatus.GATE_PENDING,
                 in_pipeline=True),
    ]
    since = {
        "1": now - timedelta(minutes=180),
        "2": now - timedelta(minutes=95),
        "3": now - timedelta(minutes=28),
    }
    metrics = compute_flow_metrics(_fake_status(steps, since))
    assert "metrics" in metrics and "by_step" in metrics
    m = metrics["metrics"]
    assert m["cycle_time_avg_minutes"] == pytest.approx(101.0, abs=3)  # (180+95+28)/3
    assert m["block_time_avg_minutes"] == pytest.approx(28.0, abs=2)
    assert "by_step" in metrics
    assert "3" in metrics["by_step"]


def test_compute_stale_rate():
    """Stale rate = cards AWAITING_HUMAN além do SLA / total awaiting."""
    now = datetime.now()
    steps = [
        StepInfo(id="3", name="PRDs", status=StepStatus.GATE_PENDING,
                 in_pipeline=True),
        StepInfo(id="4", name="Gate 5", status=StepStatus.GATE_PENDING,
                 in_pipeline=True),
    ]
    since = {
        "3": now - timedelta(minutes=45),  # stale (SLA 30)
        "4": now - timedelta(minutes=10),  # ok
    }
    metrics = compute_flow_metrics(_fake_status(steps, since), sla_minutes=30)
    assert metrics["metrics"]["stale_rate_percent"] == 50


def test_compute_first_pass_rate():
    """First-pass = steps sem REWORK / total in_pipeline."""
    now = datetime.now()
    steps = [
        StepInfo(id="1", name="Visao", status=StepStatus.COMPLETED,
                 in_pipeline=True),
        StepInfo(id="4", name="Plan", status=StepStatus.FAILED,
                 in_pipeline=True),  # rework
        StepInfo(id="5", name="Dev", status=StepStatus.COMPLETED,
                 in_pipeline=True),
    ]
    since = {"1": now - timedelta(minutes=180), "4": now - timedelta(minutes=60),
             "5": now - timedelta(minutes=120)}
    metrics = compute_flow_metrics(_fake_status(steps, since))
    assert metrics["metrics"]["first_pass_rate_percent"] == pytest.approx(66.7, abs=1)


def test_compute_skips_steps_without_history():
    """Regressão review: steps sem sessão (epoch 1970) não explodem o avg."""
    now = datetime.now()
    steps = [
        StepInfo(id="1", name="Visao", status=StepStatus.COMPLETED,
                 in_pipeline=True),
        StepInfo(id="9", name="Delta", status=StepStatus.PENDING,
                 in_pipeline=True),  # nunca iniciado → epoch
    ]
    since = {"1": now - timedelta(minutes=180),
             "9": datetime.fromtimestamp(0)}
    metrics = compute_flow_metrics(_fake_status(steps, since))
    # step sem histórico é excluído: avg = apenas o step 1 (180 min)
    assert metrics["metrics"]["cycle_time_avg_minutes"] == pytest.approx(180, abs=3)
    assert "9" not in metrics["by_step"]


def test_export_flow_metrics_creates_results_dir(tmp_path):
    """Export cria o diretório .ace/evals/results/ se ausente (RF-W1.2.3)."""
    ace = tmp_path / ".ace"
    ace.mkdir(parents=True)
    (ace / "index.json").write_text('{"sessions": []}', encoding="utf-8")
    (ace / "config").mkdir()
    (ace / "config" / "gates.json").write_text("{}", encoding="utf-8")

    path = export_flow_metrics(tmp_path)
    assert path.exists()
    assert "flow-metrics-" in path.name


def test_export_flow_metrics_marks_baseline(tmp_path):
    """RF-W1.2.4: baseline true na primeira exportação, false na segunda."""
    import yaml

    ace = tmp_path / ".ace"
    ace.mkdir(parents=True)
    (ace / "index.json").write_text('{"sessions": []}', encoding="utf-8")
    (ace / "config").mkdir()
    (ace / "config" / "gates.json").write_text("{}", encoding="utf-8")

    p1 = export_flow_metrics(tmp_path)
    d1 = yaml.safe_load(p1.read_text(encoding="utf-8"))
    assert d1["baseline"] is True

    p2 = export_flow_metrics(tmp_path)
    d2 = yaml.safe_load(p2.read_text(encoding="utf-8"))
    assert d2["baseline"] is False
