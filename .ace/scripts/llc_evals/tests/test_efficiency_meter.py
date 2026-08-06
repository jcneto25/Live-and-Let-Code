"""Testes para llc_evals.evaluators.efficiency_meter — RF-EF1.5 (PRP-EVALS-F1).

EfficiencyScore = QualityScore / log10(TokenCost)  (ADR-0005 §2.3)
"""
import pytest

from llc_evals.evaluators import efficiency_meter


def test_token_cost_sums_in_and_out():
    assert efficiency_meter.token_cost(12000, 3500) == 15500


def test_efficiency_score_formula():
    """ADR §2.3: EfficiencyScore = QualityScore / log10(TokenCost).

    Nota (correção 2026-08-06): PRP RF-EF1.5 / ADR §8.3 citavam "≈18.9" para
    QualityScore=86, TokenCost=15500, mas 86/log10(15500) = 86/4.1903 ≈ 20.52.
    O valor 18.9 é erro aritmético nos dois documentos; a fórmula do ADR §2.3
    (fonte de verdade) é implementada corretamente aqui.
    """
    assert efficiency_meter.efficiency_score(86, 15500) == pytest.approx(20.52, abs=0.01)


def test_efficiency_score_rejects_nonpositive_cost():
    with pytest.raises(ValueError):
        efficiency_meter.efficiency_score(86, 0)
    with pytest.raises(ValueError):
        efficiency_meter.efficiency_score(86, -5)
