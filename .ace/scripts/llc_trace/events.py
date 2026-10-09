"""llc_trace.events — log de eventos append-only (`.ace/logs/events.jsonl`).

Fase 0 (LLC 2.0) — instrumentacao SEM mudanca de comportamento. Contrato:

  INV-T1  nenhuma funcao deste modulo levanta excecao para o chamador;
  INV-T2  nenhuma funcao altera o valor de retorno de quem a chama;
  INV-T3  desligavel por ambiente (`LLC_TRACE=0`), util em CI e testes;
  INV-T4  append-only — nunca reescreve linha existente.

Formato de linha (JSONL, uma por evento):

    {"schema":"llc-trace-event/0.1","seq":1,"ts":"...","pid":7,
     "kind":"step.start","session_id":"...","step":"5",
     "input_hash":"sha256:...","fields":{...}}
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .hashing import input_hash

SCHEMA = "llc-trace-event/0.1"

# .ace/logs — resolvido a partir de __file__ (nao de cwd), porque o harness
# invoca subprocessos com cwd variavel.
_ACE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_TRACE_DIR = _ACE_DIR / "logs"
EVENTS_FILENAME = "events.jsonl"

# Campos longos (prompts, outputs) sao truncados: o log e evidencia, nao
# armazenamento. O conteudo integral continua acessivel pelo input_hash.
MAX_FIELD_LEN = 512

_lock = threading.Lock()
_seq = 0
_context: dict[str, Any] = {}
_disabled_explicitly = os.environ.get("LLC_TRACE", "").strip().lower() in (
    "0", "off", "false", "no",
)


# ── Configuração ────────────────────────────────────────────────────────────

def trace_dir() -> Path:
    """Diretorio dos logs. `LLC_TRACE_DIR` tem precedencia (usado em testes)."""
    override = os.environ.get("LLC_TRACE_DIR", "").strip()
    return Path(override) if override else DEFAULT_TRACE_DIR


def enabled() -> bool:
    """Instrumentacao ativa? Desligavel por `LLC_TRACE=0`."""
    return not _disabled_explicitly


def events_path() -> Path:
    return trace_dir() / EVENTS_FILENAME


# ── Contexto (session_id / step) ────────────────────────────────────────────

def set_context(**kwargs: Any) -> None:
    """Define contexto corrente (session_id, step, ...). Chaves None sao dropadas."""
    with _lock:
        for key, value in kwargs.items():
            if value is None:
                _context.pop(key, None)
            else:
                _context[key] = value


def get_context() -> dict[str, Any]:
    with _lock:
        return dict(_context)


def clear_context() -> None:
    with _lock:
        _context.clear()


def reset_for_tests() -> None:
    """Reseta contador e contexto (testes apenas)."""
    global _seq
    with _lock:
        _seq = 0
        _context.clear()


# ── Escrita ─────────────────────────────────────────────────────────────────

def _compact(value: Any, max_len: int = MAX_FIELD_LEN) -> Any:
    """Trunca strings longas e normaliza tipos para JSON."""
    if isinstance(value, str):
        return value if len(value) <= max_len else value[:max_len] + "…[truncated]"
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {k: _compact(v, max_len) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_compact(v, max_len) for v in value]
    return str(value)[:max_len]


def _append(path: Path, record: dict[str, Any]) -> dict[str, Any] | None:
    """Append de uma linha JSONL. Nunca levanta (INV-T1)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(record, ensure_ascii=False, default=str, sort_keys=True)
            )
            fh.write("\n")
            fh.flush()
        return record
    except Exception:  # noqa: BLE001 — instrumentacao nunca derruba o pipeline
        return None


def log_event(kind: str, **fields: Any) -> dict[str, Any] | None:
    """Registra um evento. Retorna o record gravado, ou None se desabilitado/falho."""
    if not enabled():
        return None
    global _seq
    with _lock:
        _seq += 1
        seq = _seq
    ctx = get_context()
    record: dict[str, Any] = {
        "schema": SCHEMA,
        "seq": seq,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "pid": os.getpid(),
        "kind": kind,
    }
    for key in ("session_id", "step", "prp", "wave"):
        value = fields.pop(key, None) or ctx.get(key)
        if value is not None:
            record[key] = value
    # `input_hash` e campo de primeira classe (nao vai para dentro de fields):
    # e a chave de correlacao com os Decision Records e com o replay futuro.
    explicit_hash = fields.pop("input_hash", None)
    hash_value = explicit_hash or ctx.get("input_hash")
    if hash_value:
        record["input_hash"] = hash_value
    compacted = {k: _compact(v) for k, v in fields.items() if v is not None}
    if compacted:
        record["fields"] = compacted
    return _append(events_path(), record)


def event_from_payload(kind: str, payload: Any, **fields: Any) -> dict[str, Any] | None:
    """Atalho: registra evento com `input_hash` calculado do payload."""
    return log_event(kind, input_hash=input_hash(payload), **fields)


def _monotonic() -> float:
    """Relogio monotonico para duracoes (nao e timestamp de parede)."""
    return time.monotonic()
