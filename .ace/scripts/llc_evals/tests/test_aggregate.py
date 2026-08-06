"""Testes para llc_evals.aggregate — RF-EF2.3/2.5 (PRP-EVALS-F2).

FirstPassRate(step) = gates_aprovados_1a_vez / total_gates
ReworkWaste(step)   = tokens_gastos_em_retries / TokenCost
(ADR-0005 §2.3) — persistência em .ace/evals/results/step-{id}-{date}.yaml
"""
from pathlib import Path

import pytest
import yaml

from llc_evals import aggregate


def test_first_pass_rate_correct():
    """RF-EF2.5: FirstPassRate = aprovados_1a_vez / total."""
    assert aggregate.first_pass_rate(gates_first_try=3, total_gates=4) == pytest.approx(0.75)


def test_first_pass_rate_zero_total():
    assert aggregate.first_pass_rate(gates_first_try=0, total_gates=0) == 0.0


def test_rework_waste_correct():
    """RF-EF2.5: ReworkWaste = tokens_retries / TokenCost."""
    assert aggregate.rework_waste(retry_tokens=2500, token_cost=10000) == pytest.approx(0.25)


def test_rework_waste_zero_cost():
    assert aggregate.rework_waste(retry_tokens=0, token_cost=0) == 0.0


def test_aggregate_with_retry_history():
    """RF-EF2.5: aggregate() a partir do histórico de retries da sessão."""
    metrics = aggregate.aggregate(
        total_gates=4,
        gates_first_try=3,
        retry_tokens=2500,
        token_cost=10000,
    )
    assert metrics["first_pass_rate"] == pytest.approx(0.75)
    assert metrics["rework_waste"] == pytest.approx(0.25)


def test_save_result_creates_yaml(tmp_path):
    """RF-EF2.3: save_result() cria YAML em .ace/evals/results/."""
    results_dir = tmp_path / ".ace" / "evals" / "results"
    path = aggregate.save_result(
        step_id="11",
        result={"code_quality": 91.9, "first_pass_rate": 0.75},
        results_dir=results_dir,
        date="2026-08-06",
    )
    assert path.exists()
    assert path.name.startswith("step-11-")
    assert path.name.endswith(".yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["step_id"] == "11"
    assert data["code_quality"] == 91.9
    assert data["date"] == "2026-08-06"


def test_save_result_creates_dir_if_missing(tmp_path):
    results_dir = tmp_path / "novo" / "results"
    path = aggregate.save_result(
        step_id="5", result={"ok": True}, results_dir=results_dir, date="2026-08-06",
    )
    assert path.exists()
    assert path.parent == results_dir
