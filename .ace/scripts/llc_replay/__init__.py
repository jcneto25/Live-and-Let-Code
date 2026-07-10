"""
LLC Deterministic Replay Engine.

Gerencia o ciclo: gravar -> buscar -> reproduzir execucoes aprovadas.
- Cache em .ace/cache/{type}.json com atomic writes (R6)
- Match por exact type + keyword overlap (A)
- Pre-flight check antes de cada write (C)
- Zone check para arquivos RED (R2)
- Gate steps mid-execucao para pausas humanas
- Rollback via git checkout em falha parcial (R5)
- Metricas em .ace/logs/replay.jsonl (D)
"""

from .constants import CACHE_DIR, LOGS_DIR, RED_ZONE_PATTERNS
from .cache import (
    atomic_cache_read,
    atomic_cache_write,
    load_cache,
    record_script,
)
from .match import extract_entities, find_best_script
from .zones import (
    check_target_files_stale,
    get_architecture_version,
    is_red_zone,
    preflight_all_steps,
    substitute,
)
from .execute import (
    ReplayError,
    deterministic_replay,
    execute_step,
    extract_files_from_script,
    log_replay_event,
)

__all__ = [
    "CACHE_DIR",
    "LOGS_DIR",
    "RED_ZONE_PATTERNS",
    "atomic_cache_read",
    "atomic_cache_write",
    "load_cache",
    "record_script",
    "extract_entities",
    "find_best_script",
    "check_target_files_stale",
    "get_architecture_version",
    "is_red_zone",
    "preflight_all_steps",
    "substitute",
    "ReplayError",
    "deterministic_replay",
    "execute_step",
    "extract_files_from_script",
    "log_replay_event",
]
