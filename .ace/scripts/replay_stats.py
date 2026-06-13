#!/usr/bin/env python3
"""LLC Replay Metrics Dashboard."""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

LOGS_FILE = Path(".ace/logs/replay.jsonl")


def main():
    if not LOGS_FILE.exists():
        print("Nenhum dado de replay encontrado. Execute algumas tarefas primeiro.")
        sys.exit(0)

    events = []
    for line in LOGS_FILE.read_text(encoding='utf-8').strip().split('\n'):
        if line:
            events.append(json.loads(line))

    since_days = 30
    cutoff = (datetime.now() - timedelta(days=since_days)).isoformat()
    events = [e for e in events if e.get("timestamp", "") >= cutoff]

    hits = sum(1 for e in events if e["event"] == "replay_hit")
    misses = sum(1 for e in events if e["event"] == "replay_miss")
    successes = sum(1 for e in events if e["event"] == "replay_success")
    rollbacks = sum(1 for e in events if e["event"] == "replay_rollback")
    llm_fallbacks = sum(1 for e in events if e["event"] == "llm_fallback")
    total = hits + misses

    print(f"\nReplay Stats (ultimos {since_days} dias):")
    if total + llm_fallbacks > 0:
        print(f"- Total tarefas:     {total + llm_fallbacks}")
        print(f"- Classificadas:     {total} ({total/(total+llm_fallbacks)*100:.1f}%)")
    else:
        print("- Total tarefas:     0")
        print("- Classificadas:     0")

    if total > 0:
        print(f"- Hits:              {hits} ({hits/total*100:.1f}% das classificadas)")
    else:
        print("- Hits:              0")

    if hits > 0:
        print(f"- Sucessos:          {successes} ({successes/hits*100:.1f}% dos hits)")
        print(f"- Rollbacks:         {rollbacks} ({rollbacks/hits*100:.1f}%)")
    else:
        print("- Sucessos:          0")
        print("- Rollbacks:         0")

    print(f"- Tokens economizados: ~{hits * 5000:,}")
    print(f"- Tempo economizado:   ~{hits * 15 // 60} minutos")


if __name__ == "__main__":
    main()
