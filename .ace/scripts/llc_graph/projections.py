"""llc_graph.projections — projeções read-only do grafo (ADR-0004 §2.8).

PRP-GRAPH-1C:
- `to_kanban()` — mapeia NodeState → KanbanColumn (PRP §3).
- `GraphPipelineDataSource` — adapter que implementa o Protocol
  `PipelineDataSource` (ADR-0002 §7.1) sobre o GraphEngine, injetado no
  `KanbanBoardBuilder` SEM refactor (GOV-003/R3). Importa de
  `llc_wizard.data` apenas dados declarativos (`REGISTRY` + tipos) e de
  `llc_wizard.kanban` apenas `KanbanColumn` — exceção documentada do
  adapter (ADR-0004 §8.3); nenhuma LÓGICA do Wizard é importada. O
  `REGISTRY` vem do binding `llc_wizard.data` (patchável nos testes de
  paridade — mesma fonte do reader).

Projeções são queries puras (P5): nenhuma muta o grafo nem as sessões ACE.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import llc_wizard.data as _wizard_data

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

def _registry():
    """REGISTRY lido dinamicamente de `llc_wizard.data` (fix review P2).

    Binding em call-time (não snapshot de import): os testes de paridade
    monkeypatch `llc_wizard.data.REGISTRY` e o adapter precisa enxergar a
    MESMA fonte estrutural do reader (`PipelineDataReader` referencia o nome
    do módulo em call-time — espelhamos isso aqui).
    """
    return _wizard_data.REGISTRY

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

    # ── get_status(): PipelineStatus com paridade de FORMA ao reader (§7.6) ─
    def get_status(self) -> PipelineStatus:
        """PipelineStatus com paridade de forma e ordem ao PipelineDataReader.

        Iteramos o REGISTRY (mesma fonte do reader, via `llc_wizard.data`)
        e derivamos o status dos nós STEP do grafo para steps in_pipeline.
        Steps fora do pipeline (excluídos — ausentes do grafo por construção)
        aparecem como `EXCLUDED`/`in_pipeline=False`, exatamente como o reader
        — a sidebar do Wizard não perde os 🚫 (fix review P2).
        """
        status_by_id: dict[str, StepStatus] = {}
        for node in self.engine.graph.nodes.values():
            if node.kind != NodeKind.STEP:
                continue
            state = self.engine.node_state(node.id)
            step_id = node.id[len("step-"):]
            status_by_id[step_id] = self._to_step_status(step_id, state)
        steps = []
        for spec in _registry().values():
            if spec.in_pipeline:
                steps.append(StepInfo(
                    id=spec.id,
                    name=self._step_name(spec.id),
                    status=status_by_id.get(spec.id, StepStatus.PENDING),
                    in_pipeline=True,
                ))
            else:
                steps.append(StepInfo(
                    id=spec.id,
                    name=spec.name,
                    status=StepStatus.EXCLUDED,
                    in_pipeline=False,
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
        spec = _registry().get(step_id)
        if spec is None or not spec.gate:
            return False
        gates = self._load_gates()
        if spec.gate not in gates:
            return False
        return self.engine.step_gate_decision(step_id) is None

    def _step_name(self, step_id: str) -> str:
        spec = _registry().get(step_id)
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

    def critical_step_ids(self) -> list[str]:
        """Ids dos steps no caminho crítico do grafo (P2b / ADR-0004 §2.7).

        `critical_path()` retorna nós (STEP + GATE + artefatos); aqui filtramos
        apenas `NodeKind.STEP` e removemos o prefixo `step-` — os ids resultam
        nos `step_id` dos cards do Kanban. Método específico do adapter
        (não faz parte do Protocol) — o Wizard acessa via duck-typing; a fonte
        `index` simplesmente não o expõe (sem marcador, comportamento atual).
        """
        return [
            n.id[len("step-"):]
            for n in self.engine.critical_path()
            if n.kind is NodeKind.STEP and n.id.startswith("step-")
        ]

    def ready_step_ids(self) -> list[str]:
        """Ids dos steps elegíveis para execução AGORA (P2b-rest / RF-W1A.7).

        `ready_nodes()` retorna nós READY e AWAITING_HUMAN (deps satisfeitas);
        aqui filtramos apenas `NodeKind.STEP` em estado READY — steps que o
        agente pode iniciar imediatamente (sem espera humana), removendo o
        prefixo `step-`. Sugestão de próximo step na coluna BACKLOG do Kanban.
        Método específico do adapter (não faz parte do Protocol) — o Wizard
        acessa via duck-typing; a fonte `index` não o expõe.
        """
        ready = [
            n for n in self.engine.ready_nodes()
            if n.kind is NodeKind.STEP
            and self.engine.node_state(n.id) is NodeState.READY
            and n.id.startswith("step-")
        ]
        return [n.id[len("step-"):] for n in ready]

    def _load_gates(self) -> dict:
        path = Path(self.engine.root) / ".ace" / "config" / "gates.json"
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("gates", {})
        except (json.JSONDecodeError, OSError):
            return {}


# ── Projeções — PRP-GRAPH-2B ────────────────────────────────────────────────

def to_impact_map(engine: GraphEngine, node_id: str) -> dict:
    """Projeção de impacto (ADR-0004 §2.8): nó + afetados ordenados.

    Query pura sobre `impact_of` — consumido pelo Delta Δ.0 / Smart Skip.
    Determinístico: `affected` ordenado por id (RF-G2B.3 parity).
    """
    return {
        "node": node_id,
        "affected": sorted(engine.impact_of(node_id)),
    }


def to_critical_path(engine: GraphEngine) -> list:
    """Projeção do caminho crítico (ADR-0004 §2.8, RF-G2B.4).

    Retorna a lista de node_ids do caminho, em ordem topológica.
    Query pura — delega ao engine.critical_path().
    """
    return [n.id for n in engine.critical_path()]
