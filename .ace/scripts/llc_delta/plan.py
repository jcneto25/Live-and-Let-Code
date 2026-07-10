#!/usr/bin/env python3
"""Integracao do plano delta com o pipeline de execucao."""

from .report import delta_report_exists, parse_delta_report


def get_delta_steps(delta_plan: dict | None) -> list[str]:
    """Retorna a lista de steps a executar no modo delta.

    Inclui steps de analise (0.2, 0.3) se DELTA_REPORT.md ainda nao existir,
    mais os steps listados em execute_steps do relatorio.
    """
    steps = []

    if delta_plan is None or not delta_report_exists():
        # Delta ainda nao iniciado — precisa executar Δ.0 primeiro
        steps.append("0.2")  # Delta Impact Analysis
        steps.append("0.3")  # Delta Grill Me
    else:
        # Delta ja analisado — executar steps planejados
        for step_id in delta_plan.get("execute_steps", []):
            steps.append(step_id)

    return steps
