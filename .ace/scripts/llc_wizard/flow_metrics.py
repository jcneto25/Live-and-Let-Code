"""llc_wizard.flow_metrics — métricas de fluxo + export YAML (PRP-WIZARD-1.2).

RF-W1.2.3/.4 — calcula Cycle Time, Block Time, Stale Rate e First-Pass Rate a
partir do PipelineDataSource (Protocol, ADR-0004 §2.3 — não acopla a leitores
concretos) e exporta para `.ace/evals/results/flow-metrics-{date}.yaml`.
A primeira exportação é marcada `baseline: true` (RF-W1.2.4).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from llc_wizard.data import StepStatus

_RESULTS_REL = Path(".ace") / "evals" / "results"


def _minutes_between(start: datetime, end: datetime | None = None) -> float:
    """Minutos entre `start` e agora (ou `end`). Nunca negativo."""
    end = end or datetime.now()
    delta = (end - start).total_seconds() / 60
    return max(0.0, delta)


def compute_flow_metrics(source, sla_minutes: int = 30) -> dict:
    """Calcula métricas de fluxo agregadas + por step (RF-W1.2.3).

    Retorna {"metrics": {...}, "by_step": {...}} no formato do PRP §3:
    - cycle_time_avg_minutes: média do tempo em coluna (status_since → agora)
    - block_time_avg_minutes: média do tempo em AWAITING_HUMAN
    - stale_rate_percent: % de cards AWAITING_HUMAN além do SLA
    - first_pass_rate_percent: % de steps sem rework (não FAILED)
    """
    status = source.get_status()
    now = datetime.now()
    epoch = datetime.fromtimestamp(0)

    cycle_times: list[float] = []
    block_times: list[float] = []
    awaiting_total = 0
    awaiting_stale = 0
    first_pass = 0
    total = 0
    by_step: dict[str, dict] = {}

    for step in status.steps:
        if not step.in_pipeline:
            continue
        since = source.get_status_since(step.id)
        # steps sem histórico (nunca iniciados → status_since = epoch 1970)
        # não contribuem para métricas de fluxo (evita ~29M min no avg)
        if since is None or since <= epoch:
            continue
        cycle = _minutes_between(since, now)
        is_awaiting = step.status is StepStatus.GATE_PENDING
        block = cycle if is_awaiting else 0.0

        if is_awaiting:
            awaiting_total += 1
            if cycle > sla_minutes:
                awaiting_stale += 1

        fp = step.status is not StepStatus.FAILED
        if fp:
            first_pass += 1
        total += 1

        entry: dict = {
            "cycle_time": round(cycle),
            "block_time": round(block),
            "first_pass": fp,
        }
        if step.status is StepStatus.FAILED:
            entry["rework_count"] = 1
        by_step[step.id] = entry

        cycle_times.append(cycle)
        if block > 0:  # média de block time considera apenas steps bloqueados
            block_times.append(block)

    metrics = {
        "cycle_time_avg_minutes": round(
            sum(cycle_times) / len(cycle_times)) if cycle_times else 0,
        "block_time_avg_minutes": round(
            sum(block_times) / len(block_times)) if block_times else 0,
        "stale_rate_percent": round(
            awaiting_stale / awaiting_total * 100) if awaiting_total else 0,
        "first_pass_rate_percent": round(
            first_pass / total * 100) if total else 0,
    }
    return {"metrics": metrics, "by_step": by_step}


def export_flow_metrics(project_root, source=None,
                        results_dir=None) -> Path:
    """Gera `.ace/evals/results/flow-metrics-{date}.yaml` (RF-W1.2.3).

    Primeira exportação (nenhum flow-metrics-*.yaml existente) é marcada
    `baseline: true` (RF-W1.2.4). Retorna o caminho do arquivo gravado.
    """
    import yaml

    root = Path(project_root)
    if source is None:
        from llc_wizard.data import PipelineDataReader

        source = PipelineDataReader(root)
    if results_dir is None:
        results_dir = root / _RESULTS_REL
    results = Path(results_dir)
    results.mkdir(parents=True, exist_ok=True)

    existing = list(results.glob("flow-metrics-*.yaml"))
    payload = compute_flow_metrics(source)
    payload["generated_at"] = datetime.now().isoformat(timespec="seconds")
    payload["baseline"] = not existing  # RF-W1.2.4: baseline apenas na 1ª

    filename = f"flow-metrics-{datetime.now():%Y-%m-%d}.yaml"
    path = results / filename
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path
