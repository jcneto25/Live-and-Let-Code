"""llc_graph.projections — projeções read-only do grafo (ADR-0004 §2.8).

PRP-GRAPH-1C:
- `to_kanban()` — mapeia NodeState → KanbanColumn (PRP §3).
- `GraphPipelineDataSource` — adapter que implementa o Protocol
  `PipelineDataSource` (ADR-0002 §7.1) sobre o GraphEngine, injetado no
  `KanbanBoardBuilder` SEM refactor (GOV-003/R3). Importa apenas TIPOS de
  dados de `llc_wizard.data`/`llc_wizard.kanban` — exceção documentada do
  adapter (ADR-0004 §8.3); nenhuma lógica do Wizard é importada.

Projeções são queries puras (P5): nenhuma muta o grafo nem as sessões ACE.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from llc_steps import REGISTRY

from llc_graph.engine import GraphEngine
from llc_graph.model import NodeKind, NodeState
from llc_wizard.data import (
    GateInfo,
    GateItem,
    PendingHITL,
    PipelineStatus,
    StepInfo,
    StepStatus,
)
from llc_wizard.kanban import KanbanColumn

# PRP-GRAPH-1C §3 — mapeamento NodeState → coluna Kanban
NODE_STATE_TO_COLUMN = {
    NodeState.PENDING: KanbanColumn.BACKLOG,
    NodeState.READY: KanbanColumn.BACKLOG,
    NodeState.RUNNING: KanbanColumn.RUNNING,
    NodeState.AWAITING_HUMAN: KanbanColumn.AWAITING_HUMAN,
    NodeState.FAILED: KanbanColumn.REWORK,
    NodeState.DONE: KanbanColumn.DONE,
    NodeState.SKIPPED: KanbanColumn.SKIPPED,
}

# NodeState → StepStatus (semântica do PipelineDataReader §7.6)
_NODE_STATE_TO_STATUS = {
    NodeState.PENDING: StepStatus.PENDING,
    NodeState.READY: StepStatus.PENDING,          # elegível, não iniciado
    NodeState.RUNNING: StepStatus.IN_PROGRESS,
    NodeState.AWAITING_HUMAN: StepStatus.GATE_PENDING,
    NodeState.FAILED: StepStatus.FAILED,
    NodeState.DONE: StepStatus.COMPLETED,
    NodeState.SKIPPED: StepStatus.SKIPPED,
}


def to_kanban(node_state: NodeState) -> KanbanColumn:
    """Mapeia NodeState → KanbanColumn (RF-G1C.1/2, PRP-GRAPH-1C §3)."""
    return NODE_STATE_TO_COLUMN[node_state]


class GraphPipelineDataSource:
    """Adapter: implementa PipelineDataSource (ADR-0002 §7.1) sobre o GraphEngine.

    RF-G1C.3: o KanbanBoardBuilder continua recebendo o Protocol — apenas a
    implementação injetada muda (PipelineDataReader → GraphPipelineDataSource).
    RF-G1C.5: `get_status_since()` usa o timestamp real da sessão ACE.
    """

    def __init__(self, engine: GraphEngine):
        self.engine = engine

    # ── get_status(): PipelineStatus a partir dos nós STEP do grafo ─────────
    def get_status(self) -> PipelineStatus:
        steps = []
        for node in self.engine.graph.nodes.values():
            if node.kind != NodeKind.STEP:
                continue
            state = self.engine.node_state(node.id)
            step_id = node.id[len("step-"):]
            steps.append(StepInfo(
                id=step_id,
                name=self._step_name(step_id),
                status=self._to_step_status(step_id, state),
                in_pipeline=True,
            ))
        return PipelineStatus(steps=steps)

    def _to_step_status(self, step_id: str, state: NodeState) -> StepStatus:
        """NodeState → StepStatus com paridade ao PipelineDataReader §7.6.

        O engine mantém RUNNING para sessão in_progress; o reader, porém,
        mostra GATE_PENDING quando o step tem gate e nenhuma decisão foi
        registrada (item 3 da tabela §7.6). Espelhamos isso aqui para
        paridade 100% (RF-G1C.4).
        """
        status = _NODE_STATE_TO_STATUS[state]
        if (status is StepStatus.IN_PROGRESS
                and self._has_undecided_gate(step_id)):
            return StepStatus.GATE_PENDING
        return status

    def _has_undecided_gate(self, step_id: str) -> bool:
        """Step tem gate (gates.json) e nenhuma decisão registrada ainda."""
        spec = REGISTRY.get(step_id)
        if spec is None or not spec.gate:
            return False
        gates = self._load_gates()
        if spec.gate not in gates:
            return False
        return self.engine.step_gate_decision(step_id) is None

    def _step_name(self, step_id: str) -> str:
        spec = REGISTRY.get(step_id)
        return spec.name if spec is not None else step_id

    # ── Demais métodos do Protocol (paridade com PipelineDataReader) ────────
    def get_gate_for_step(self, step_id: str) -> GateInfo | None:
        gate_def = self._load_gates().get(step_id)
        if not gate_def:
            return None
        items = []
        checklist = (
            gate_def.get("checklist", []) if isinstance(gate_def, dict) else gate_def
        )
        for idx, text in enumerate(checklist, start=1):
            items.append(GateItem(id=str(idx), description=str(text)))
        return GateInfo(id=step_id, items=items)

    def get_status_since(self, step_id: str) -> datetime:
        """Timestamp real da última sessão ativa do step (RF-G1C.5)."""
        return self.engine.session_timestamp(step_id)

    def get_pending_hitl(self) -> list[PendingHITL]:
        return []

    def _load_gates(self) -> dict:
        path = Path(self.engine.root) / ".ace" / "config" / "gates.json"
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("gates", {})
        except (json.JSONDecodeError, OSError):
            return {}


# ── Stubs — implementados em PRP-GRAPH-2B ────────────────────────────────────

def to_impact_map(engine: GraphEngine, node_id: str) -> dict:
    """Projeção de impacto → PRP-GRAPH-2B (stub por enquanto)."""
    raise NotImplementedError("to_impact_map → PRP-GRAPH-2B")


def to_critical_path(engine: GraphEngine) -> list:
    """Projeção de caminho crítico → PRP-GRAPH-2B (stub por enquanto)."""
    raise NotImplementedError("to_critical_path → PRP-GRAPH-2B")
