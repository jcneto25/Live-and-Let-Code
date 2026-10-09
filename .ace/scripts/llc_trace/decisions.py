"""llc_trace.decisions — Decision Records versionados (`.ace/logs/decisions.jsonl`).

Fase 0 (LLC 2.0). O objetivo e que a Fase 7 (Deterministic Replay) consuma
este arquivo sem re-inferencia. Por isso o registro ja nasce no formato-alvo,
mesmo que LLC 1.x nao tenha Jev, Decision Policy nem Statechart: os campos
existem e valem `null`.

    Regra de ouro: Decision Record responde "por que o runtime decidiu X?"
    — nao "o que o agente disse?".

Formato de linha (JSONL):

    {"schema":"llc-trace-decision/0.1","decision_id":"...","ts":"...",
     "kind":"early_commitment","session_id":"...","step":"5",
     "state":"STEP_EXECUTION","event":"REPLAY_MISS",
     "input_hash":"sha256:...","state_hash":null,
     "inputs":{...},"evidence":{...},
     "outcome":"llm_fallback","reason":"no_classify",
     "automation":"AUTO",
     "policy_version":null,"statechart_version":null,
     "jev_model":null,"jev_request_id":null,"jev_result":null,
     "hard_eval":null,"human_approval":null,
     "statechart":null,"risk_class":null,"question_set":null,
     "runtime_version":"llc-1.x","config":{...}}

Campos `null` nao sao omitidos de proposito: registro incompleto e diferente
de registro ausente, e a omissao silenciosa e o que torna auditoria impossivel
quando a Fase 2/4/6 comecar a preenche-los.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .events import _append, _compact, enabled, get_context, trace_dir
from .hashing import input_hash

SCHEMA = "llc-trace-decision/0.1"
DECISIONS_FILENAME = "decisions.jsonl"
RUNTIME_VERSION = "llc-1.x"

# ── Kinds de decisão instrumentados na Fase 0 ───────────────────────────────
EARLY_COMMITMENT = "early_commitment"
GATE = "gate"
SMART_SKIP = "smart_skip"
STEP_EXECUTION = "step_execution"


def decisions_path() -> Path:
    return trace_dir() / DECISIONS_FILENAME


def record_decision(
    kind: str,
    outcome: Any = None,
    *,
    reason: str | None = None,
    state: str | None = None,
    event: str | None = None,
    inputs: Any = None,
    input_hash_value: str | None = None,
    state_hash: str | None = None,
    evidence: Any = None,
    automation: str | None = None,
    hard_eval: Any = None,
    human_approval: Any = None,
    session_id: str | None = None,
    step: str | None = None,
    config: Any = None,
    # ── Insumos de replay (solução A): gravados p/ verificação §12 ──
    statechart: Any = None,
    jev_result: Any = None,
    risk_class: str | None = None,
    question_set: Any = None,
) -> dict[str, Any] | None:
    """Grava um Decision Record. Nunca levanta; retorna None se desabilitado.

    `inputs` e opcional: quando fornecido, `input_hash` e derivado dele
    (a menos que `input_hash_value` seja passado explicitamente).
    """
    if not enabled():
        return None

    ctx = get_context()
    session_id = session_id or ctx.get("session_id")
    step = step if step is not None else ctx.get("step")

    if input_hash_value is None:
        input_hash_value = input_hash(inputs) if inputs is not None else None

    record: dict[str, Any] = {
        "schema": SCHEMA,
        "decision_id": str(uuid.uuid4()),
        "ts": datetime.now().isoformat(timespec="seconds"),
        "pid": os.getpid(),
        "kind": kind,
        "session_id": session_id,
        "step": str(step) if step is not None else None,
        "state": state,
        "event": event,
        "input_hash": input_hash_value,
        "state_hash": state_hash,
        "inputs": _compact(inputs) if inputs is not None else None,
        "evidence": _compact(evidence) if evidence is not None else None,
        "outcome": outcome,
        "reason": reason,
        "automation": automation,
        # ── Campos do LLC 2.0 — ausentes em 1.x, preservados como null ──
        "policy_version": None,
        "statechart_version": None,
        "jev_model": None,
        "jev_request_id": None,
        "jev_result": _compact(jev_result) if jev_result is not None else None,
        "hard_eval": _compact(hard_eval) if hard_eval is not None else None,
        "human_approval": human_approval,
        # ── Insumos de replay (solução A) — null quando não gravados ──
        "statechart": _compact(statechart) if statechart is not None else None,
        "risk_class": risk_class,
        "question_set": _compact(question_set) if question_set is not None else None,
        "runtime_version": RUNTIME_VERSION,
        "config": _compact(config) if config is not None else None,
    }
    return _append(decisions_path(), record)
