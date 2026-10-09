"""llc_trace.stats — leitura e resumo dos logs de Fase 0 (read-only).

Entrega o baseline REAL de custo do LLC 1.x, que a Passagem 4 estimou e que
so a instrumentacao pode medir:

  - replay hit rate (quantas execucoes evitaram LLM);
  - motivos de fallback (`no_classify`, `cache_miss`, `stale_cache`, ...);
  - decisoes de gate (approved / rejected / auto_approve / no_gate);
  - eventos e decisoes por sessao (calls/session);
  - linhas corrompidas (perda de evidencia — deve ser 0).

Nunca escreve em disco.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .decisions import decisions_path
from .events import events_path


def read_jsonl(path: str | Path) -> tuple[list[dict], int]:
    """Le um arquivo JSONL tolerando linhas corrompidas.

    Retorna (registros_validos, linhas_corrompidas).
    """
    p = Path(path)
    if not p.exists():
        return [], 0
    records: list[dict] = []
    corrupt = 0
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [], 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            corrupt += 1
            continue
        if isinstance(obj, dict):
            records.append(obj)
        else:
            corrupt += 1
    return records, corrupt


def _counter(values: list[Any]) -> dict[str, int]:
    return dict(Counter(str(v) for v in values if v is not None))


def summarize(events: list[dict], decisions: list[dict],
              corrupt_events: int = 0, corrupt_decisions: int = 0) -> dict:
    """Agrega eventos e decisoes no resumo de baseline."""
    ec = _counter([e.get("kind") for e in events])
    dc = _counter([d.get("kind") for d in decisions])

    by_outcome = _counter([d.get("outcome") for d in decisions])
    by_reason: dict[str, int] = {}
    for d in decisions:
        if d.get("reason"):
            by_reason[str(d["reason"])] = by_reason.get(str(d["reason"]), 0) + 1

    # Decisoes de early commitment = o coracao do gap G1 (replay 0% hit).
    ec_decisions = [d for d in decisions if d.get("kind") == "early_commitment"]
    ec_outcomes = _counter([d.get("outcome") for d in ec_decisions])
    ec_reasons = _counter([d.get("reason") for d in ec_decisions])
    replay_hits = ec_outcomes.get("replay_hit", 0)
    replay_total = len(ec_decisions)
    hit_rate = (replay_hits / replay_total) if replay_total else None

    gate_decisions = [d for d in decisions if d.get("kind") == "gate"]
    gate_outcomes = _counter([d.get("outcome") for d in gate_decisions])
    gate_reasons = _counter([d.get("reason") for d in gate_decisions])

    sessions = _counter([e.get("session_id") for e in events])
    decisions_per_session = _counter([d.get("session_id") for d in decisions])

    llm_calls = ec_outcomes.get("llm_fallback", 0)

    return {
        "events_total": len(events),
        "decisions_total": len(decisions),
        "corrupt_lines": {"events": corrupt_events, "decisions": corrupt_decisions},
        "events_by_kind": ec,
        "decisions_by_kind": dc,
        "decisions_by_outcome": by_outcome,
        "decisions_by_reason": by_reason,
        "early_commitment": {
            "total": replay_total,
            "by_outcome": ec_outcomes,
            "by_reason": ec_reasons,
            "replay_hits": replay_hits,
            "replay_hit_rate": hit_rate,
            "llm_fallbacks": llm_calls,
        },
        "gates": {
            "total": len(gate_decisions),
            "by_outcome": gate_outcomes,
            "by_reason": gate_reasons,
        },
        "sessions": {
            "total": len(sessions),
            "events_by_session": sessions,
            "decisions_by_session": decisions_per_session,
            "avg_decisions_per_session": (
                round(len(decisions) / len(sessions), 2) if sessions else None
            ),
        },
    }


def load_summary(events_file: str | Path | None = None,
                 decisions_file: str | Path | None = None) -> dict:
    """Le os arquivos (default: os do projeto) e devolve o resumo."""
    ev, ce = read_jsonl(events_file or events_path())
    de, cd = read_jsonl(decisions_file or decisions_path())
    return summarize(ev, de, ce, cd)


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def format_text(summary: dict) -> str:
    """Relatorio textual de leitura humana."""
    ec = summary["early_commitment"]
    g = summary["gates"]
    s = summary["sessions"]
    corrupt = summary["corrupt_lines"]
    total_corrupt = corrupt["events"] + corrupt["decisions"]

    lines = [
        "=" * 60,
        "LLC TRACE — BASELINE (Fase 0, instrumentacao)",
        "=" * 60,
        f"Eventos: {summary['events_total']}   Decisoes: {summary['decisions_total']}",
        f"Linhas corrompidas: {total_corrupt}"
        + ("  ⚠️  perda de evidencia" if total_corrupt else "  ✅"),
        "",
        "── Early Commitment / Replay " + "─" * 30,
        f"Decisoes: {ec['total']}   Replay hits: {ec['replay_hits']}"
        f"   Hit rate: {_pct(ec['replay_hit_rate'])}",
        f"Fallbacks para LLM: {ec['llm_fallbacks']}",
    ]
    if ec["by_outcome"]:
        lines.append("Por outcome:")
        for k, v in sorted(ec["by_outcome"].items(), key=lambda kv: -kv[1]):
            lines.append(f"  {k:<16} {v}")
    if ec["by_reason"]:
        lines.append("Por motivo:")
        for k, v in sorted(ec["by_reason"].items(), key=lambda kv: -kv[1]):
            lines.append(f"  {k:<16} {v}")

    lines += ["", "── Gates " + "─" * 42, f"Decisoes de gate: {g['total']}"]
    if g["by_outcome"]:
        for k, v in sorted(g["by_outcome"].items(), key=lambda kv: -kv[1]):
            lines.append(f"  {k:<16} {v}")
    if g["by_reason"]:
        lines.append("Por motivo (origem da decisao):")
        for k, v in sorted(g["by_reason"].items(), key=lambda kv: -kv[1]):
            lines.append(f"  {k:<16} {v}")

    lines += [
        "",
        "── Sessoes " + "─" * 40,
        f"Sessoes com eventos: {s['total']}"
        f"   Decisoes/sessao (media): {s['avg_decisions_per_session']}",
    ]
    if summary["events_by_kind"]:
        lines += ["", "── Eventos por kind " + "─" * 32]
        for k, v in sorted(summary["events_by_kind"].items(), key=lambda kv: -kv[1]):
            lines.append(f"  {k:<24} {v}")
    lines.append("")
    return "\n".join(lines)
