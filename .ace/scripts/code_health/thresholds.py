#!/usr/bin/env python3
"""code-health — verificação de thresholds e geração de alertas."""

from .coverage import check_coverage_thresholds, check_coverage_trends


def check_thresholds(
    stats: dict,
    age: dict,
    coverage: dict | None = None,
    coverage_thresholds: dict | None = None,
    coverage_history: list[dict] | None = None,
) -> list[dict]:
    """Verifica thresholds e gera alertas."""
    alerts = []

    if stats.get("pct_moved", 0) < 10:
        alerts.append(
            {
                "severity": "critical",
                "metric": "Moved Code %",
                "value": f"{stats['pct_moved']}%",
                "threshold": "≥ 10%",
                "message": "Perda estrutural de manutenibilidade. Código não está sendo reorganizado em módulos.",
                "action": "Identificar blocos duplicados e propor refatoração cross-PRP.",
            }
        )

    if stats.get("copy_est", 0) > stats.get("moved_min", 0):
        alerts.append(
            {
                "severity": "high",
                "metric": "Copy/Paste vs Moved",
                "value": f"copy={stats['copy_est']} moved={stats['moved_min']}",
                "threshold": "copy ≤ moved",
                "message": "Duplicação superando reuso. Princípio DRY em risco.",
                "action": "Revisar PRPs recentes: consolidar código duplicado em módulo compartilhado.",
            }
        )

    if age.get("pct_legacy_touched", 30) < 20:
        alerts.append(
            {
                "severity": "high",
                "metric": "Legacy Code Touch %",
                "value": f"{age['pct_legacy_touched']}%",
                "threshold": "≥ 20%",
                "message": "Código antigo (>30 dias) não está sendo refatorado. Agentes focam apenas em novas linhas.",
                "action": "Agendar onda de refatoração de código legacy nos próximos PRPs.",
            }
        )

    # Coverage checks
    if coverage:
        if coverage_thresholds:
            alerts.extend(check_coverage_thresholds(coverage, coverage_thresholds))
        if coverage_history:
            alerts.extend(check_coverage_trends(coverage, coverage_history))

    if not alerts:
        alerts.append(
            {
                "severity": "ok",
                "metric": "Code Health",
                "value": "Todos os thresholds OK",
                "threshold": "—",
                "message": "Saúde estrutural do código dentro dos parâmetros.",
                "action": "Manter monitoramento nas próximas ondas.",
            }
        )

    return alerts
