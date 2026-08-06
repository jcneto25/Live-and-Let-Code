"""llc_evals.report — Dashboard Pareto (Custo × Qualidade) + ranking (PRP-EVALS-F5).

ADR-0005 §2.10 (Reporting): responde "qual step é o maior gargalo de custo?"
com dados puros:
- `rank_by_efficiency()`    — steps por EfficiencyScore crescente (pior → melhor)
- `rank_by_rework_waste()`  — steps por ReworkWaste decrescente (maior → menor)
- `generate_report()`       — Markdown `.ace/evals/results/report-{date}.md`
- `build_eval_summary()`    — resumo consumido pelo `code-health.py` (RF-EF5.4)

DIP: importa apenas stdlib + `llc_evals.aggregate` (intra-pacote). Nenhuma
dependência de `llc_wizard`/`llc_harness`.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from llc_evals.aggregate import BaselineManager


def rank_by_efficiency(steps: list[dict]) -> list[dict]:
    """Ordena steps por EfficiencyScore crescente — menor = pior custo-benefício.

    RF-EF5.1: pior → melhor (gargalo de eficiência no topo).
    Determinístico: estável (mesma ordem relativa preservada em empates).
    """
    return sorted(steps, key=lambda s: s["efficiency_score"])


def rank_by_rework_waste(steps: list[dict]) -> list[dict]:
    """Ordena steps por ReworkWaste decrescente — maior = mais tokens perdidos.

    RF-EF5.2: maior desperdício primeiro.
    """
    return sorted(steps, key=lambda s: s["rework_waste"], reverse=True)


def load_efficiency_rows(baselines_dir: Path | str) -> list[dict]:
    """Lê baselines (BaselineManager) → linhas de eficiência por step.

    Usa o bucket do nível de precisão ativo de cada baseline; steps sem
    baseline não entram no ranking.
    """
    manager = BaselineManager(baselines_dir)
    rows: list[dict] = []
    for path in sorted(Path(baselines_dir).glob("step-*.yaml")):
        step_id = path.stem[len("step-"):]
        try:
            baseline = manager.load_baseline(step_id)
        except (yaml.YAMLError, OSError, ValueError):
            continue  # baseline malformada — skip, como load_rework_rows
        active = baseline.get("active_precision")
        bucket = baseline.get("by_precision_level", {}).get(active or "")
        if bucket is None or bucket.get("run_count", 0) == 0:
            continue
        rows.append({
            "step": step_id,
            "quality_score": bucket.get("quality_score_avg", 0.0),
            "token_cost": bucket.get("token_cost_avg", 0.0),
            "efficiency_score": bucket.get("efficiency_score_avg", 0.0),
            "phase": baseline.get("baseline_phase", "collecting"),
        })
    return rows


def load_rework_rows(results_dir: Path | str) -> list[dict]:
    """Lê resultados salvos (save_result) → linhas de rework por step.

    Arquivo: `step-{id}-{date}.yaml` com `rework_waste` (fração 0-1) e retries.
    `step_id` vem do campo `data.step_id`; fallback: segunda parte do filename
    (sobrevive a ids pontuados como `11.1`).
    """
    rows: list[dict] = []
    for path in sorted(Path(results_dir).glob("step-*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError):
            continue
        step_id = data.get("step_id") or path.stem.split("-")[1]
        rows.append({
            "step": str(step_id),
            "rework_waste": float(data.get("rework_waste", 0.0)),
            "retries": int(data.get("retries", 0)),
        })
    return rows


def generate_report(
    *,
    baselines_dir: Path | str,
    results_dir: Path | str,
    output_dir: Path | str,
    report_date: str | None = None,
) -> Path:
    """Gera o relatório Markdown Pareto (RF-EF5.3).

    Arquivo: `{output_dir}/report-{date}.md`. Cria diretório se necessário.
    Inclui as duas tabelas Pareto + fase de baseline de cada step (DoD).
    """
    day = report_date or str(date.today())
    eff_rows = rank_by_efficiency(load_efficiency_rows(baselines_dir))
    rework_rows = rank_by_rework_waste(load_rework_rows(results_dir))

    lines = [f"# Eval Report — {day}", ""]
    lines.append("## Pareto: Eficiência por Step (pior → melhor)")
    lines.append("| Step | QualityScore | TokenCost | EfficiencyScore | Fase |")
    lines.append("|------|-------------|-----------|-----------------|------|")
    for r in eff_rows:
        lines.append(
            f"| {r['step']} | {r['quality_score']:g} | {r['token_cost']:g} "
            f"| {r['efficiency_score']:g} | {r['phase']} |"
        )
    lines.append("")
    lines.append("## Pareto: Desperdício de Rework (maior → menor)")
    lines.append("| Step | ReworkWaste% | Retries |")
    lines.append("|------|-------------|---------|")
    for r in rework_rows:
        lines.append(f"| {r['step']} | {r['rework_waste'] * 100:.0f}% | {r['retries']} |")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"report-{day}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_eval_summary(
    *,
    baselines_dir: Path | str,
    results_dir: Path | str,
) -> dict:
    """Resumo para o code-health.py — seção "Eval Summary" (RF-EF5.4).

    Retorna o pior step em eficiência, o maior em rework waste e a contagem
    de steps analisados. `None` nos topo quando não há dados (sem exceção).
    """
    eff_rows = load_efficiency_rows(baselines_dir)
    rework_rows = load_rework_rows(results_dir)
    worst = rank_by_efficiency(eff_rows)
    top_waste = rank_by_rework_waste(rework_rows)
    return {
        "steps_analyzed": len(eff_rows),
        "steps_with_results": len(rework_rows),
        "worst_efficiency": worst[0] if worst else None,
        "highest_rework_waste": top_waste[0] if top_waste else None,
    }
