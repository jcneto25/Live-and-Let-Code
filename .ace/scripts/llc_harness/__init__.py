#!/usr/bin/env python3
"""llc_harness — modulo de orquestracao do pipeline Live and Let Code.

Pacote resultante do refactor clean-code (sub-projeto 2). Submódulos:
  - common:     constantes compartilhadas + loader de gates.json
  - gates:      resolução de checklist + gate_check (checkpoint humano)
  - session:    session_start/end, resolução de index, bloqueio de merge PRP
  - replay:     detecção de CLI, agent_invoke, Early Commitment + Replay
  - skill:      skill_load (progressive disclosure) + convenções do AGENTS.md
  - pipeline:   pipeline_run, _run_delta_analysis, step_run

Este __init__ re-exporta a API completa para manter
`from llc_harness import ...` e `import llc_harness; llc_harness.<nome>`
funcionando para llc.py, llc_wave/run.py e os testes.
"""

from .common import (
    ACE_DIR,
    AGENTS_FILE,
    CONFIG_DIR,
    GATES_FILE,
    SCRIPTS_DIR,
    SKILLS_DIR,
    load_gates_config,
)
from .gates import gate_check, get_gate_checklist
from .replay import (
    CLASSIFY_REPLAY_AVAILABLE,
    agent_invoke,
    detect_agent_client,
    _llm_invoke,
)
from .session import (
    _maybe_block_on_prp_verify,
    _prp_from_index,
    _record_gate_result,
    _resolve_session,
    _run_prp_verify,
    _step_from_index,
    SESSIONS_DIR,
    session_end,
    session_start,
)
from .skill import load_agents_conventions, skill_load
from .pipeline import _run_delta_analysis, pipeline_run, step_run

__all__ = [
    "ACE_DIR",
    "AGENTS_FILE",
    "CONFIG_DIR",
    "GATES_FILE",
    "SCRIPTS_DIR",
    "SKILLS_DIR",
    "SESSIONS_DIR",
    "load_gates_config",
    "gate_check",
    "get_gate_checklist",
    "CLASSIFY_REPLAY_AVAILABLE",
    "agent_invoke",
    "detect_agent_client",
    "_llm_invoke",
    "_maybe_block_on_prp_verify",
    "_prp_from_index",
    "_record_gate_result",
    "_resolve_session",
    "_run_prp_verify",
    "_step_from_index",
    "session_end",
    "session_start",
    "load_agents_conventions",
    "skill_load",
    "_run_delta_analysis",
    "pipeline_run",
    "step_run",
]
