"""LLC 2.0 — Projeção macro: UMA fonte de verdade para a orquestração.

Problema que este módulo resolve
--------------------------------
A Passagem 3 deixou dois "núcleos determinísticos" coexistentes:

  1. `contracts.TRANSITIONS`  — `NodeMachine`, uma instância por nó
                                (step/PRP/gate). Micro. Executável, puro,
                                sem dependências.
  2. `llc_statechart_corrigido.py` — `LLCPipeline`, máquina macro
                                (discovery → planning → implementation →
                                deploy), com `human_gate`, `self_heal` e
                                região paralela `quality_gates`. Depende de
                                `python-statemachine >= 3.2`.

Dois statecharts = duas autoridades de transição. É exatamente a falha que
a Passagem 1 §3.5 e a Passagem 2 §0.3 proíbem.

Decisão (D-A)
-------------
**A máquina macro é rebaixada a PROJEÇÃO DERIVADA.** Ela não transiciona,
não guarda estado próprio e não é fonte de verdade: é uma função pura das
configurações das `NodeMachine`.

    macro_view(configs) -> MacroView        # puro, determinístico

A hierarquia continua existindo (é hierarquia de Harel legítima), mas a
composição é explícita e testável: o estado macro é *função* do estado
micro, nunca o contrário. `llc_statechart_corrigido.py` permanece como
artefato de documentação executável — desde que suas divergências com o
runtime real estejam listadas em `divergences()`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

# ── tabela de fases ────────────────────────────────────────────────────────
# NOTA DE IMPLEMENTAÇÃO (Fase 0): esta tabela deve ser GERADA de
# `.ace/scripts/llc_steps/registry.py`, não mantida à mão. Aqui é canônica
# apenas para fins de especificação.
PHASE_BY_PREFIX: tuple[tuple[str, str], ...] = (
    ("0", "discovery"),      # 0, 0.1-0.3 (delta), 0.5, 1, 2
    ("1", "discovery"),
    ("2", "discovery"),
    ("3", "planning"),
    ("4", "planning"),
    ("5", "planning"),       # 5, 5.1-5.4
    ("6", "planning"),
    ("7", "planning"),
    ("8", "implementation"),
    ("9", "implementation"),
    ("10", "implementation"),  # 10, 10.5, 10.6 ...
    ("11", "implementation"),
)

_SUBSTATE_OF_NODE: dict[str, str] = {
    "0": "discovery.ingestion",
    "0.5": "discovery.vision",
    "1": "discovery.specs",
    "2": "discovery.prd_generation",
    "3": "planning.prp_generation",
    "4": "planning.planning_waves",
    "5": "planning.architecture",
    "6": "planning.tasks",
}

TERMINAL_STATES = frozenset({"done", "skipped"})
FAILED_STATES = frozenset({"failed"})


def phase_of(node_id: str) -> str:
    """Fase macro de um nó. 'unmapped' se fora da tabela (falha explícita)."""
    for prefix, phase in PHASE_BY_PREFIX:
        if node_id == prefix or node_id.startswith(prefix + "."):
            return phase
    return "unmapped"


def substate_of(node_id: str, state_id: str) -> str:
    if state_id.startswith("governance"):
        return "governance"
    if state_id in TERMINAL_STATES | FAILED_STATES:
        return state_id
    return _SUBSTATE_OF_NODE.get(node_id, f"{phase_of(node_id)}.{node_id}")


@dataclass(frozen=True)
class MacroView:
    phase: str                 # discovery | planning | implementation |
                               # governance | terminal | unmapped | empty
    substate: str
    per_phase: Mapping[str, Mapping[str, int]]
    blocked_by_human: tuple[str, ...]
    failed: tuple[str, ...]

    def as_dict(self) -> dict:
        return {"phase": self.phase, "substate": self.substate,
                "per_phase": dict(self.per_phase),
                "blocked_by_human": list(self.blocked_by_human),
                "failed": list(self.failed)}


def macro_view(configs: Mapping[str, str]) -> MacroView:
    """PROJEÇÃO PURA. `configs`: {node_id: state_id_da_NodeMachine}.

    Precedência:
      1. algum nó em `governance.awaiting_human` -> "governance"
      2. algum nó ativo (não terminal)           -> fase do nó mais adiantado
      3. todos terminais                         -> "terminal"
    """
    if not configs:
        return MacroView("empty", "", {}, (), ())

    per_phase: dict[str, dict[str, int]] = {}
    human: list[str] = []
    failed: list[str] = []

    for node_id, state_id in sorted(configs.items()):
        phase = phase_of(node_id)
        bucket = per_phase.setdefault(
            phase, {"total": 0, "done": 0, "skipped": 0,
                    "failed": 0, "active": 0, "awaiting_human": 0})
        bucket["total"] += 1
        if state_id.startswith("governance.awaiting_human"):
            bucket["awaiting_human"] += 1
            human.append(node_id)
        elif state_id in FAILED_STATES:
            bucket["failed"] += 1
            failed.append(node_id)
        elif state_id in TERMINAL_STATES:
            bucket[state_id] += 1
        else:
            bucket["active"] += 1

    if human:
        first = sorted(human)[0]
        return MacroView("governance", substate_of(first, configs[first]),
                         per_phase, tuple(sorted(human)), tuple(sorted(failed)))

    active = [n for n, s in sorted(configs.items())
              if s not in TERMINAL_STATES and s not in FAILED_STATES]
    if active:
        head = active[0]
        return MacroView(phase_of(head), substate_of(head, configs[head]),
                         per_phase, (), tuple(sorted(failed)))

    return MacroView("terminal", "terminal", per_phase, (), tuple(sorted(failed)))


# ── divergências do chart macro original ───────────────────────────────────

#: estados de `llc_statechart_corrigido.py` que a projeção NÃO produz.
UNPRODUCED_MACRO_STATES = (
    "discovery.use_cases",   # não existe step "casos de uso" no registry
    "self_heal",             # virou `governance.rework` na NodeMachine
    "deployed",              # `deploy` é FORBIDDEN_EVERYWHERE
)

#: capacidades que o chart macro permitia e a matriz de capacidade proíbe.
FORBIDDEN_IN_MACRO_CHART = ("deploy",)


def divergences() -> tuple[str, ...]:
    """Lista auditável do que o chart macro original tem além do runtime."""
    return tuple(
        [f"estado sem origem no registry: {s}" for s in UNPRODUCED_MACRO_STATES]
        + [f"ação proibida pela matriz: {a}" for a in FORBIDDEN_IN_MACRO_CHART]
    )
