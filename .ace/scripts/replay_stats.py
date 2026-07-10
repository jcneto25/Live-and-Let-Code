#!/usr/bin/env python3
"""LLC Replay Metrics Dashboard.

Carrega o log JSONL de replay e calcula métricas de hit/miss, sucessos,
rollbacks e fallbacks para LLM nos últimos `since_days` dias.

Funções puras (`load_events`, `filter_recent`, `compute_stats`) extraídas
para permitir characterization tests sem I/O de disco.
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

LOGS_FILE = Path(".ace/logs/replay.jsonl")
DEFAULT_SINCE_DAYS = 30


def load_events(logs_file: Path) -> list:
    """Lê o JSONL de replay e retorna a lista de eventos (vazio se ausente)."""
    if not logs_file.exists():
        return []
    events = []
    for line in logs_file.read_text(encoding="utf-8").strip().split("\n"):
        if line:
            events.append(json.loads(line))
    return events


def filter_recent(events: list, since_days: int = DEFAULT_SINCE_DAYS) -> list:
    """Mantém apenas eventos com timestamp >= cutoff (agora - since_days)."""
    cutoff = (datetime.now() - timedelta(days=since_days)).isoformat()
    return [e for e in events if e.get("timestamp", "") >= cutoff]


def compute_stats(events: list, since_days: int = DEFAULT_SINCE_DAYS) -> dict:
    """Calcula as métricas agregadas a partir dos eventos filtrados."""
    hits = sum(1 for e in events if e["event"] == "replay_hit")
    misses = sum(1 for e in events if e["event"] == "replay_miss")
    successes = sum(1 for e in events if e["event"] == "replay_success")
    rollbacks = sum(1 for e in events if e["event"] == "replay_rollback")
    llm_fallbacks = sum(1 for e in events if e["event"] == "llm_fallback")
    total = hits + misses
    return {
        "since_days": since_days,
        "total_tasks": total + llm_fallbacks,
        "classified": total,
        "hits": hits,
        "misses": misses,
        "successes": successes,
        "rollbacks": rollbacks,
        "llm_fallbacks": llm_fallbacks,
        "tokens_saved": hits * 5000,
        "minutes_saved": hits * 15 // 60,
    }


def _render(stats: dict) -> None:
    """Imprime o dashboard (saída primária do programa)."""
    s = stats
    sd = s["since_days"]
    total = s["classified"]
    lf = s["llm_fallbacks"]

    print(f"\nReplay Stats (ultimos {sd} dias):")
    if total + lf > 0:
        print(f"- Total tarefas:     {total + lf}")
        print(f"- Classificadas:     {total} ({total / (total + lf) * 100:.1f}%)")
    else:
        print("- Total tarefas:     0")
        print("- Classificadas:     0")

    if total > 0:
        print(f"- Hits:              {s['hits']} ({s['hits'] / total * 100:.1f}% das classificadas)")
    else:
        print("- Hits:              0")

    if s["hits"] > 0:
        print(f"- Sucessos:          {s['successes']} ({s['successes'] / s['hits'] * 100:.1f}% dos hits)")
        print(f"- Rollbacks:         {s['rollbacks']} ({s['rollbacks'] / s['hits'] * 100:.1f}%)")
    else:
        print("- Sucessos:          0")
        print("- Rollbacks:         0")

    print(f"- Tokens economizados: ~{s['tokens_saved']:,}")
    print(f"- Tempo economizado:   ~{s['minutes_saved']} minutos")


def main() -> int:
    if not LOGS_FILE.exists():
        logger.info("Nenhum dado de replay encontrado. Execute algumas tarefas primeiro.")
        return 0

    events = load_events(LOGS_FILE)
    stats = compute_stats(filter_recent(events))
    _render(stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
