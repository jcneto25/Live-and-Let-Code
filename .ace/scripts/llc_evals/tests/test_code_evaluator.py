"""Testes para llc_evals.evaluators.code_evaluator — RF-EF2.1/2.2/2.4 (PRP-EVALS-F2).

CodeQuality = w1·pass_rate + w2·fitness_score + w3·coverage + w4·consistency
(ADR-0005 §2.8). Pesos padrão configuráveis via gates.json → evals.code_weights.
"""
import json
from pathlib import Path

import pytest

from llc_evals.evaluators import code_evaluator


def test_default_weights_code_quality():
    """RF-EF2.1: score correto com pesos padrão ∈ [0,100].

    pass_rate=0.9, fitness=38/40=0.95, coverage=0.87, consistency=True:
    0.40*0.9 + 0.30*0.95 + 0.20*0.87 + 0.10*1.0 = 0.919 → 91.9
    """
    evaluator = code_evaluator.CodeEvaluator()
    score = evaluator.evaluate(
        pass_rate=0.9,
        fitness_checks=38,
        fitness_total=40,
        coverage=0.87,
        consistency=True,
    )
    assert score == pytest.approx(91.9, abs=0.01)
    assert 0.0 <= score <= 100.0


def test_determinism_same_input_same_score():
    """RF-EF2.4: mesma entrada → mesmo score (N chamadas)."""
    evaluator = code_evaluator.CodeEvaluator()
    kwargs = dict(
        pass_rate=0.9, fitness_checks=38, fitness_total=40,
        coverage=0.87, consistency=True,
    )
    results = {evaluator.evaluate(**kwargs) for _ in range(5)}
    assert len(results) == 1


def test_consistency_false_reduces_score():
    evaluator = code_evaluator.CodeEvaluator()
    base = evaluator.evaluate(
        pass_rate=0.9, fitness_checks=38, fitness_total=40,
        coverage=0.87, consistency=True,
    )
    lower = evaluator.evaluate(
        pass_rate=0.9, fitness_checks=38, fitness_total=40,
        coverage=0.87, consistency=False,
    )
    assert lower == pytest.approx(base - 10.0, abs=0.01)  # w4=0.10 * 1.0 * 100


def test_custom_weights_from_gates_json(tmp_path):
    """RF-EF2.2: pesos customizados em gates.json → evals.code_weights."""
    gates_path = tmp_path / "gates.json"
    gates_path.write_text(json.dumps({
        "evals": {
            "code_weights": {
                "pass_rate": 0.5, "fitness": 0.3,
                "coverage": 0.1, "consistency": 0.1,
            }
        }
    }), encoding="utf-8")

    evaluator = code_evaluator.CodeEvaluator(gates_path=gates_path)
    score = evaluator.evaluate(
        pass_rate=0.8, fitness_checks=40, fitness_total=40,
        coverage=0.5, consistency=True,
    )
    # 0.5*0.8 + 0.3*1.0 + 0.1*0.5 + 0.1*1.0 = 0.85 → 85.0
    assert score == pytest.approx(85.0, abs=0.01)


def test_default_weights_used_when_no_evals_config(tmp_path):
    gates_path = tmp_path / "gates.json"
    gates_path.write_text(json.dumps({"gates": {}}), encoding="utf-8")
    evaluator = code_evaluator.CodeEvaluator(gates_path=gates_path)
    assert evaluator.weights == code_evaluator.DEFAULT_WEIGHTS


def test_routes_to_code_and_test_steps():
    """Roteamento: steps de código (11) e testes (9, 10.8) → True."""
    evaluator = code_evaluator.CodeEvaluator()
    assert evaluator.routes_to("11")
    assert evaluator.routes_to("9")
    assert evaluator.routes_to("10.8")
    assert not evaluator.routes_to("0.5")
    assert not evaluator.routes_to("2")


def test_fitness_score_fraction():
    evaluator = code_evaluator.CodeEvaluator()
    score = evaluator.evaluate(
        pass_rate=1.0, fitness_checks=40, fitness_total=40,
        coverage=1.0, consistency=True,
    )
    assert score == pytest.approx(100.0, abs=0.01)
