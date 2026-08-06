"""llc_evals.evaluators.code_evaluator — agregação de qualidade de código.

PRP-EVALS-F2 (ADR-0005 §2.8): CodeQuality unifica mecanismos já existentes
(pytest, fitness-functions, coverage, consistency-check) num score único
[0,100]. Não recria nada — apenas agrega (P2).

    CodeQuality = (w1·pass_rate + w2·fitness_score + w3·coverage + w4·consistency) * 100

Pesos padrão configuráveis via gates.json → evals.code_weights (RF-EF2.2).
Determinístico: mesma entrada → mesmo score (RF-EF2.4).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

DEFAULT_WEIGHTS = {
    "pass_rate": 0.40,   # pytest pass rate
    "fitness": 0.30,     # fitness-functions.py score (checks passed / total)
    "coverage": 0.20,    # pytest --cov coverage %
    "consistency": 0.10,  # consistency-check.py pass/fail
}

# Steps roteados para CodeEvaluator (ADR-0005 §2.6): código + testes.
_CODE_STEPS = {"11", "9", "10.8", "10.9"}


def _load_weights(gates_path: Optional[Path]) -> dict:
    """Lê evals.code_weights de gates.json; default se ausente/corrompido."""
    if gates_path is None or not gates_path.exists():
        return dict(DEFAULT_WEIGHTS)
    try:
        data = json.loads(gates_path.read_text(encoding="utf-8"))
        weights = (data.get("evals") or {}).get("code_weights")
    except (json.JSONDecodeError, OSError, AttributeError):
        return dict(DEFAULT_WEIGHTS)
    if not isinstance(weights, dict) or not weights:
        return dict(DEFAULT_WEIGHTS)
    merged = dict(DEFAULT_WEIGHTS)
    merged.update({k: float(v) for k, v in weights.items()})
    return merged


class CodeEvaluator:
    """Avaliador determinístico de qualidade de código (RF-EF2.1/2.2/2.4)."""

    def __init__(self, gates_path: Optional[Path | str] = None):
        self._gates_path = Path(gates_path) if gates_path else None
        self.weights = _load_weights(self._gates_path)

    def evaluate(
        self,
        *,
        pass_rate: float,
        fitness_checks: int,
        fitness_total: int,
        coverage: float,
        consistency: bool,
    ) -> float:
        """CodeQuality ∈ [0,100] a partir dos mecanismos existentes."""
        fitness_score = (
            fitness_checks / fitness_total if fitness_total > 0 else 0.0
        )
        consistency_score = 1.0 if consistency else 0.0
        scores = {
            "pass_rate": pass_rate,
            "fitness": fitness_score,
            "coverage": coverage,
            "consistency": consistency_score,
        }
        quality = sum(
            self.weights.get(key, 0.0) * scores[key]
            for key in ("pass_rate", "fitness", "coverage", "consistency")
        )
        return round(quality * 100, 2)

    def routes_to(self, step_id: str) -> bool:
        """True para steps de código/testes (ADR-0005 §2.6 roteamento)."""
        return step_id in _CODE_STEPS
