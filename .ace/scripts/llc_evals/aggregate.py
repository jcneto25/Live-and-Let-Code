"""llc_evals.aggregate — agregação de métricas por step + persistência.

PRP-EVALS-F2 (ADR-0005 §2.3, §2.9):
    FirstPassRate(step) = gates_aprovados_1a_vez / total_gates
    ReworkWaste(step)   = tokens_gastos_em_retries / TokenCost

save_result() persiste em .ace/evals/results/step-{id}-{date}.yaml (RF-EF2.3).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml


def first_pass_rate(*, gates_first_try: int, total_gates: int) -> float:
    """Gates aprovados de primeira / total (ADR-0005 §2.3)."""
    if total_gates <= 0:
        return 0.0
    return round(gates_first_try / total_gates, 4)


def rework_waste(*, retry_tokens: float, token_cost: float) -> float:
    """Fração de tokens desperdiçada em retries (ADR-0005 §2.3)."""
    if token_cost <= 0:
        return 0.0
    return round(retry_tokens / token_cost, 4)


def aggregate(
    *,
    total_gates: int,
    gates_first_try: int,
    retry_tokens: float,
    token_cost: float,
) -> dict:
    """Métricas agregadas da sessão a partir do histórico de retries (RF-EF2.5)."""
    return {
        "first_pass_rate": first_pass_rate(
            gates_first_try=gates_first_try, total_gates=total_gates,
        ),
        "rework_waste": rework_waste(
            retry_tokens=retry_tokens, token_cost=token_cost,
        ),
    }


def save_result(
    *,
    step_id: str,
    result: dict,
    results_dir: Path,
    date: str | None = None,
) -> Path:
    """Persiste resultado em `.ace/evals/results/step-{id}-{date}.yaml` (RF-EF2.3)."""
    day = date or str(date.today())
    path = Path(results_dir) / f"step-{step_id}-{day}.yaml"
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "step_id": step_id,
        "date": day,
        **result,
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path
