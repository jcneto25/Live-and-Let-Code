"""llc_evals.flow_report — Relatório de Gargalos Reais (P4 pos-roadmap).

Cruza o caminho crítico do GraphEngine (ADR-0004 §2.7) com as métricas de
fluxo exportadas pelo Wizard (flow-metrics-*.yaml — PRP-WIZARD-1.2,
RF-W1.2.3):

- **Gargalo acionável** — step NO caminho crítico com `block_time > 0`
  (espera humana: gate/humano parado) ou `rework_count > 0` / `first_pass
  false` (retrabalho). Ação: aprovar o gate / investigar qualidade.
- **Pacing atual** — step crítico com maior `cycle_time`: o que determina a
  duração total do pipeline hoje.

DIP: o núcleo (`compute_bottlenecks`) é puro (stdlib, sem I/O). A
orquestração (`generate_flow_report`) importa `llc_graph` de forma LAZY
(padrão do projeto — ver `llc_wizard.data.build_data_source`), evitando ciclo
de módulos e mantendo o pacote testável.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml


def compute_bottlenecks(critical_steps: list[str], flow_metrics: dict) -> dict:
    """Identifica gargalos acionáveis no caminho crítico (RF-P4.1/.2).

    Para cada step crítico com dados em `flow_metrics["by_step"]`:
    - `espera_humana` — `block_time > 0` (step parado aguardando gate/humano)
    - `retrabalho`    — `rework_count > 0` ou `first_pass is False`

    Retorna:
    - `bottlenecks`: steps com ≥1 motivo, ordenados por (nº de motivos desc,
      block_time desc) — mais acionável no topo
    - `pacing`: `{step, cycle_time}` do crítico com maior cycle_time (ou None)
    - `critical_total` / `with_metrics` / `without_metrics` (gap de dados)

    Função pura (CQS): nenhum I/O, sem mutação. Degrada gracioso para
    entradas malformadas (nunca lança).
    """
    by_step_raw = (
        flow_metrics.get("by_step", {})
        if isinstance(flow_metrics, dict) else {}
    )
    # Normaliza chaves para str: o yaml.safe_dump do export cita chaves
    # numéricas ('3', '10.9'), mas um arquivo escrito à mão com `3:` sem
    # aspas carrega como int — a busca por string falharia e o step seria
    # silenciosamente ignorado (fix review P4). str(10.9) e str(10) casam
    # com os ids reais.
    by_step = {str(k): v for k, v in by_step_raw.items()}
    rows: list[dict] = []
    pacing: dict | None = None
    for step in critical_steps:
        data = by_step.get(step)
        if not isinstance(data, dict):
            continue
        block = int(data.get("block_time", 0) or 0)
        rework = int(data.get("rework_count", 0) or 0)
        cycle = int(data.get("cycle_time", 0) or 0)
        reasons: list[str] = []
        if block > 0:
            reasons.append("espera_humana")
        if rework > 0 or data.get("first_pass") is False:
            reasons.append("retrabalho")
        rows.append({
            "step": step,
            "reasons": reasons,
            "block_time": block,
            "rework_count": rework,
            "cycle_time": cycle,
        })
        if pacing is None or cycle > pacing["cycle_time"]:
            pacing = {"step": step, "cycle_time": cycle}
    bottlenecks = sorted(
        (r for r in rows if r["reasons"]),
        key=lambda r: (-len(r["reasons"]), -r["block_time"]),
    )
    return {
        "bottlenecks": bottlenecks,
        "pacing": pacing,
        "critical_total": len(critical_steps),
        "with_metrics": len(rows),
        "without_metrics": [s for s in critical_steps if s not in by_step],
    }


def _render_report(day: str, data: dict) -> list[str]:
    """Linhas Markdown do relatório (RF-P4.3)."""
    lines = [f"# Flow Report — {day}", ""]
    lines.append("## Caminho Crítico × Métricas de Fluxo (P4)")
    lines.append("")
    lines.append(
        f"Steps no caminho crítico: {data['critical_total']} · "
        f"com métricas: {data['with_metrics']} · "
        f"sem métricas (gap): {len(data['without_metrics'])}"
    )
    lines.append("")
    lines.append("## 🚨 Gargalos acionáveis (espera humana / retrabalho)")
    lines.append("")
    if data["bottlenecks"]:
        lines.append("| Step | Motivos | BlockTime(min) | Rework | CycleTime(min) |")
        lines.append("|------|---------|----------------|--------|----------------|")
        for b in data["bottlenecks"]:
            lines.append(
                f"| {b['step']} | {', '.join(b['reasons'])} | {b['block_time']} "
                f"| {b['rework_count']} | {b['cycle_time']} |"
            )
    else:
        lines.append("_Nenhum gargalo acionável — pipeline fluindo._")
    lines.append("")
    lines.append("## ⏱️ Pacing atual (maior cycle time no caminho crítico)")
    lines.append("")
    pacing = data["pacing"]
    if pacing:
        lines.append(
            f"Step {pacing['step']} — {pacing['cycle_time']} min "
            "(determina a duração total hoje)"
        )
    else:
        lines.append("_Sem dados de cycle time._")
    lines.append("")
    if data["without_metrics"]:
        lines.append("## 📡 Steps críticos sem métricas (gap de dados)")
        lines.append("")
        lines.append(
            "Sem dados no `flow-metrics-*.yaml` — executar "
            "`llc wizard --export-flow-metrics` para coletar:"
        )
        lines.append("")
        lines.append(", ".join(data["without_metrics"]))
    return lines


def generate_flow_report(
    *,
    project_root: Path | str,
    results_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    report_date: str | None = None,
) -> Path:
    """Gera `flow-report-{date}.md` — caminho crítico × flow metrics (P4).

    - Caminho crítico: `GraphBuilder` + `GraphEngine` sobre o projeto
      (import lazy de `llc_graph` — DIP/sem ciclo)
    - Métricas: arquivo `flow-metrics-*.yaml` MAIS RECENTE em `results_dir`
    - Degrada gracioso: sem arquivo de métricas → relatório com gap; grafo
      vazio → crítico vazio. Retorna o caminho gravado.
    """
    from llc_graph.builder import GraphBuilder  # lazy (DIP / sem ciclo)
    from llc_graph.engine import GraphEngine
    from llc_graph.model import NodeKind

    root = Path(project_root)
    results = (
        Path(results_dir) if results_dir
        else root / ".ace" / "evals" / "results"
    )
    out = Path(output_dir) if output_dir else results
    day = report_date or str(date.today())

    # 1. Caminho crítico → steps (sem prefixo `step-`)
    engine = GraphEngine(
        graph=GraphBuilder(project_root=root).build(),
        project_root=root,
    )
    critical_steps = [
        n.id[len("step-"):]
        for n in engine.critical_path()
        if n.kind is NodeKind.STEP and n.id.startswith("step-")
    ]

    # 2. Flow metrics mais recente (RF-W1.2.3)
    flow_metrics: dict = {}
    files = sorted(results.glob("flow-metrics-*.yaml"))
    if files:
        try:
            flow_metrics = yaml.safe_load(
                files[-1].read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError):
            flow_metrics = {}

    # 3. Gargalos + Markdown
    data = compute_bottlenecks(critical_steps, flow_metrics)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"flow-report-{day}.md"
    path.write_text("\n".join(_render_report(day, data)) + "\n", encoding="utf-8")
    return path
