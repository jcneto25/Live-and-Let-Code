"""llc_trace — instrumentacao do runtime LLC (Fase 0 do LLC 2.0).

Proposito: tornar o LLC 1.x observavel ANTES de muda-lo. A Passagem 4 estimou
custo, latencia e replay hit rate; este modulo e o que transforma estimativa
em medida.

Tres artefatos:
  `.ace/logs/events.jsonl`    — linha do tempo de execucao (append-only)
  `.ace/logs/decisions.jsonl` — Decision Records versionados (append-only)
  `input_hash` por step       — base para replay determinico (Fase 7)

Contrato de nao-interferencia (testado em tests/test_noninterference.py):
  INV-T1  nenhuma funcao levanta excecao para o chamador;
  INV-T2  nenhuma funcao altera o valor de retorno de quem a chama;
  INV-T3  desligavel por `LLC_TRACE=0`;
  INV-T4  append-only.

Fase 0 NAO introduz Jev, Policy nem Statechart: os campos correspondentes
existem no Decision Record e valem `null`. A Fase 7 pode entao comparar
"mesma decisao?" sem re-inferencia — e sem ambiguidade entre
"campo ausente em 1.x" e "campo nao preenchido em 2.0".
"""
from __future__ import annotations

from .decisions import (
    DECISIONS_FILENAME,
    EARLY_COMMITMENT,
    GATE,
    RUNTIME_VERSION,
    SMART_SKIP,
    STEP_EXECUTION,
    decisions_path,
    record_decision,
)
from .events import (
    EVENTS_FILENAME,
    SCHEMA as EVENT_SCHEMA,
    clear_context,
    enabled,
    event_from_payload,
    events_path,
    get_context,
    log_event,
    reset_for_tests,
    set_context,
    trace_dir,
)
from .hashing import canonical_json, hash_file, input_hash, sha256_hex
from .stats import format_text, load_summary, read_jsonl, summarize

__all__ = [
    # hashing
    "canonical_json",
    "sha256_hex",
    "input_hash",
    "hash_file",
    # events
    "log_event",
    "event_from_payload",
    "set_context",
    "get_context",
    "clear_context",
    "reset_for_tests",
    "enabled",
    "trace_dir",
    "events_path",
    "EVENTS_FILENAME",
    "EVENT_SCHEMA",
    # decisions
    "record_decision",
    "decisions_path",
    "DECISIONS_FILENAME",
    "RUNTIME_VERSION",
    "EARLY_COMMITMENT",
    "GATE",
    "SMART_SKIP",
    "STEP_EXECUTION",
    # stats
    "read_jsonl",
    "summarize",
    "load_summary",
    "format_text",
]
