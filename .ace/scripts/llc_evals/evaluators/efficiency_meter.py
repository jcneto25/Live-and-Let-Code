"""llc_evals.evaluators.efficiency_meter — TokenCost e EfficiencyScore.

PRP-EVALS-F1 (ADR-0005 §2.3):
    TokenCost(step)        = tokens_in + tokens_out
    EfficiencyScore(step)  = QualityScore / log10(TokenCost)

Funções puras (CQS — query, sem efeito colateral). Determinísticas (P5/D10).
"""
from __future__ import annotations

import math


def token_cost(tokens_in: int, tokens_out: int) -> int:
    """Custo total em tokens (somente consulta)."""
    return tokens_in + tokens_out


def efficiency_score(quality_score: float, token_cost_value: float) -> float:
    """EffEfficiency = quality_score / log10(token_cost). Exige cost > 0.

    Raise: ValueError se token_cost_value <= 0 (log10 indefinido) ou seed<0.
    """
    if token_cost_value <= 0:
        raise ValueError("token_cost_value deve ser > 0")
    if quality_score < 0:
        raise ValueError("quality_score deve ser >= 0")
    return quality_score / math.log10(token_cost_value)
