"""Testes para llc_graph.projections — RF-G1C.1 a G1C.5 (PRP-GRAPH-1C).

to_kanban(): NodeState → KanbanColumn (ADR-0004 §2.8).
GraphPipelineDataSource: adapter que implementa o Protocol PipelineDataSource
(ADR-0002 §7.1) sobre o GraphEngine — injetado no KanbanBoardBuilder SEM
refactor (GOV-003/R3). Importa apenas tipos de dados de llc_wizard
(exceção documentada do adapter — ADR-0004 §8.3).
"""
import json
from datetime import datetime
from pathlib import Path

import pytest

from llc_graph.builder import GraphBuilder
from llc_graph.engine import GraphEngine
from llc_graph.model import NodeState
from llc_graph.projections import (
    GraphPipelineDataSource,
    NODE_STATE_TO_COLUMN,
    to_critical_path,
    to_impact_map,
    to_kanban,
)
from llc_wizard.data import PipelineDataReader, StepStatus
from llc_wizard.kanban import KanbanBoardBuilder, KanbanColumn


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _registry_5_steps():
    """REGISTRY mínimo: 0.5 (gate 1), 1..4 sem gate."""
    from llc_steps.models import _spec

    return {
        "0.5": _spec("0.5", "Visão + Módulos", "llc-step-0-5", "1", True, False),
        "1": _spec("1", "7 Especificações", "llc-step-1", None, True, False),
        "2": _spec("2", "PRDs", "llc-step-2", None, True, False),
        "3": _spec("3", "PRPs", "llc-step-3", None, True, False),
        "4": _spec("4", "Planejamento", "llc-step-4", None, True, False),
    }


def _write_gates(tmp_path: Path) -> Path:
    p = tmp_path / ".ace" / "config" / "gates.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"gates": {
        "1": {"step": 0.5, "label": "Visao", "checklist": ["Revisar visão"]},
    }}), encoding="utf-8")
    return p


def _write_index(tmp_path: Path, sessions: list[dict]) -> Path:
    p = tmp_path / ".ace" / "index.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"sessions": sessions}), encoding="utf-8")
    return p


def _write_session(tmp_path: Path, session_id: str, gate_decision: str):
    """Sessão .md com <gate_result> real (não-placeholder)."""
    p = tmp_path / ".ace" / "sessions" / f"{session_id}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "---\nstatus: completed\n---\n\n"
        f'<gate_result step="0.5" decision="{gate_decision}" reviewer="harness">'
        "human gate</gate_result>\n",
        encoding="utf-8",
    )
    return p


def _ace_fixture(tmp_path: Path) -> dict:
    """ACE completo: 5 steps em estados distintos (paridade + SLA)."""
    _write_gates(tmp_path)
    _write_index(tmp_path, [
        {"session_id": "s-05", "llc_step_id": "0.5", "status": "completed",
         "timestamp": "2026-08-06T09:00:00"},
        {"session_id": "s-1", "llc_step_id": "1", "status": "in_progress",
         "timestamp": "2026-08-06T10:00:00"},
        {"session_id": "s-2", "llc_step_id": "2", "status": "failed",
         "timestamp": "2026-08-06T08:00:00"},
        {"session_id": "s-3", "llc_step_id": "3", "status": "skipped",
         "timestamp": "2026-08-06T11:00:00"},
    ])
    _write_session(tmp_path, "s-05", "approved")
    # skip-note p/ o reader enxergar step-3 como SKIPPED (mecanismo do reader)
    note = tmp_path / "docs" / "delta" / "skip-notes" / "step-3.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text("# skip\n", encoding="utf-8")

    registry = _registry_5_steps()
    builder = GraphBuilder(project_root=tmp_path, registry=registry)
    graph = builder.build()
    engine = GraphEngine(graph=graph, project_root=tmp_path)
    return {
        "registry": registry,
        "graph": graph,
        "engine": engine,
        "adapter": GraphPipelineDataSource(engine),
    }


# ── RF-G1C.1/2: to_kanban() mapeia NodeState → KanbanColumn ─────────────────

def test_to_kanban_maps_done_to_done_column():
    """RF-G1C.1: NodeState.DONE → KanbanColumn.DONE."""
    assert to_kanban(NodeState.DONE) == KanbanColumn.DONE


def test_to_kanban_maps_all_seven_states():
    """RF-G1C.2: os 7 estados mapeiam para a coluna correta (PRP §3)."""
    expected = {
        NodeState.PENDING: KanbanColumn.BACKLOG,
        NodeState.READY: KanbanColumn.BACKLOG,
        NodeState.RUNNING: KanbanColumn.RUNNING,
        NodeState.AWAITING_HUMAN: KanbanColumn.AWAITING_HUMAN,
        NodeState.FAILED: KanbanColumn.REWORK,
        NodeState.DONE: KanbanColumn.DONE,
        NodeState.SKIPPED: KanbanColumn.SKIPPED,
    }
    assert NODE_STATE_TO_COLUMN == expected
    for state, column in expected.items():
        assert to_kanban(state) == column


# ── RF-G1C.3: adapter implementa o Protocol completo ─────────────────────────

def test_adapter_builds_valid_board_without_changing_builder(tmp_path, monkeypatch):
    """RF-G1C.3: KanbanBoardBuilder(GraphPipelineDataSource(engine)).build().

    O builder continua recebendo o Protocol — nenhuma assinatura mudou.
    """
    fixture = _ace_fixture(tmp_path)
    monkeypatch.setattr("llc_wizard.data.REGISTRY", fixture["registry"])
    board = KanbanBoardBuilder(fixture["adapter"]).build()
    assert set(board.keys()) == set(KanbanColumn)
    # steps em cada coluna esperada
    assert [c.id for c in board[KanbanColumn.DONE]] == ["0.5"]
    assert [c.id for c in board[KanbanColumn.RUNNING]] == ["1"]
    assert [c.id for c in board[KanbanColumn.REWORK]] == ["2"]
    assert [c.id for c in board[KanbanColumn.SKIPPED]] == ["3"]
    assert [c.id for c in board[KanbanColumn.BACKLOG]] == ["4"]


def test_adapter_exposes_all_protocol_methods(tmp_path):
    """O adapter cobre os 4 métodos do Protocol PipelineDataSource (ADR-0002 §7.1)."""
    fixture = _ace_fixture(tmp_path)
    adapter = fixture["adapter"]
    assert callable(adapter.get_status)
    assert callable(adapter.get_gate_for_step)
    assert callable(adapter.get_status_since)
    assert callable(adapter.get_pending_hitl)


def test_adapter_get_status_maps_states_to_step_status(tmp_path, monkeypatch):
    """get_status() traduz NodeState → StepStatus (mesma semântica do reader)."""
    fixture = _ace_fixture(tmp_path)
    monkeypatch.setattr("llc_wizard.data.REGISTRY", fixture["registry"])
    status = fixture["adapter"].get_status()
    by_id = {s.id: s for s in status.steps}
    assert by_id["0.5"].status == StepStatus.COMPLETED
    assert by_id["1"].status == StepStatus.IN_PROGRESS
    assert by_id["2"].status == StepStatus.FAILED
    assert by_id["3"].status == StepStatus.SKIPPED
    assert by_id["4"].status == StepStatus.PENDING
    assert all(s.in_pipeline for s in status.steps)


def test_adapter_get_status_shape_parity_includes_excluded(tmp_path, monkeypatch):
    """P2 (fix review): paridade de FORMA — excluded steps presentes.

    O adapter itera o REGISTRY (via binding patchável de llc_wizard.data);
    steps fora do pipeline (excluídos, ausentes do grafo por construção)
    aparecem como EXCLUDED/in_pipeline=False — a sidebar do Wizard não
    perde os 🚫 ao trocar para a fonte graph.
    """
    from llc_steps.models import _spec

    fixture = _ace_fixture(tmp_path)
    # registry com step excluído (in_pipeline=False) — id numérico (o _spec
    # converte id para float no StepSpec.number)
    registry = dict(fixture["registry"])
    registry["99"] = _spec("99", "Excluido", "llc-step-99", None, False, False)
    monkeypatch.setattr("llc_wizard.data.REGISTRY", registry)

    status = fixture["adapter"].get_status()
    by_id = {s.id: s for s in status.steps}
    assert by_id["99"].status == StepStatus.EXCLUDED
    assert by_id["99"].in_pipeline is False
    assert by_id["4"].in_pipeline is True

    # paridade 1:1 com o reader (mesmo binding)
    reader_status = PipelineDataReader(tmp_path).get_status()
    reader_by_id = {s.id: (s.status, s.in_pipeline) for s in reader_status.steps}
    adapter_shape = {s.id: (s.status, s.in_pipeline) for s in status.steps}
    assert reader_by_id == adapter_shape


# ── RF-G1C.4: paridade adapter (grafo) = reader ──────────────────────────────

def test_parity_adapter_board_equals_reader_board(tmp_path, monkeypatch):
    """RF-G1C.4: mesmo estado ACE → board idêntico via adapter e via reader.

    O reader usa o REGISTRY global; para comparar 1:1, monkeypatcheamos o
    REGISTRY do módulo data com o fixture (mesma fonte de estrutura).
    """
    fixture = _ace_fixture(tmp_path)
    monkeypatch.setattr("llc_wizard.data.REGISTRY", fixture["registry"])

    board_reader = KanbanBoardBuilder(PipelineDataReader(tmp_path)).build()
    board_adapter = KanbanBoardBuilder(fixture["adapter"]).build()

    def normalize(board):
        return {
            col.value: [c.id for c in cards]
            for col, cards in board.items()
        }

    assert normalize(board_adapter) == normalize(board_reader)


def test_parity_get_status_since_matches_reader(tmp_path, monkeypatch):
    """RF-G1C.4: get_status_since() do adapter == reader (timestamps reais)."""
    fixture = _ace_fixture(tmp_path)
    monkeypatch.setattr("llc_wizard.data.REGISTRY", fixture["registry"])
    reader = PipelineDataReader(tmp_path)

    for step_id in ("0.5", "1", "2", "3", "4"):
        assert (fixture["adapter"].get_status_since(step_id)
                == reader.get_status_since(step_id))


def _ace_fixture_rejected_gate(tmp_path: Path) -> dict:
    """Variante: step 0.5 completed com gate REJEITADO (rework)."""
    _write_gates(tmp_path)
    _write_index(tmp_path, [
        {"session_id": "s-05", "llc_step_id": "0.5", "status": "completed",
         "timestamp": "2026-08-06T09:00:00"},
    ])
    _write_session(tmp_path, "s-05", "rejected")
    registry = _registry_5_steps()
    builder = GraphBuilder(project_root=tmp_path, registry=registry)
    graph = builder.build()
    engine = GraphEngine(graph=graph, project_root=tmp_path)
    return {
        "registry": registry,
        "graph": graph,
        "engine": engine,
        "adapter": GraphPipelineDataSource(engine),
    }


def test_parity_rejected_gate_adapter_equals_reader(tmp_path, monkeypatch):
    """RF-G1C.4: gate rejeitado → adapter e reader mostram FAILED/REWORK.

    Regressão (revisão GRAPH-1C): o engine retornava DONE para o step
    completado sem consultar a decisão do gate — divergia do reader §7.6.
    """
    fixture = _ace_fixture_rejected_gate(tmp_path)
    monkeypatch.setattr("llc_wizard.data.REGISTRY", fixture["registry"])

    board_reader = KanbanBoardBuilder(PipelineDataReader(tmp_path)).build()
    board_adapter = KanbanBoardBuilder(fixture["adapter"]).build()

    def normalize(board):
        return {
            col.value: [c.id for c in cards]
            for col, cards in board.items()
        }

    assert normalize(board_adapter) == normalize(board_reader)
    assert [c.id for c in board_adapter[KanbanColumn.REWORK]] == ["0.5"]
    assert board_adapter[KanbanColumn.DONE] == []


def _ace_fixture_gate_pending(tmp_path: Path) -> dict:
    """Variante: step 0.5 in_progress com gate e SEM decisão registrada.

    Reader §7.6 item 3: sessão in_progress + gate sem <gate_result> →
    GATE_PENDING (coluna AWAITING_HUMAN) — não IN_PROGRESS.
    """
    _write_gates(tmp_path)
    _write_index(tmp_path, [
        {"session_id": "s-05", "llc_step_id": "0.5", "status": "in_progress",
         "timestamp": "2026-08-06T09:00:00"},
    ])
    # sessão sem <gate_result> (gate ainda não decidido)
    p = tmp_path / ".ace" / "sessions" / "s-05.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\nstatus: in_progress\n---\n\n", encoding="utf-8")

    registry = _registry_5_steps()
    builder = GraphBuilder(project_root=tmp_path, registry=registry)
    graph = builder.build()
    engine = GraphEngine(graph=graph, project_root=tmp_path)
    return {
        "registry": registry,
        "graph": graph,
        "engine": engine,
        "adapter": GraphPipelineDataSource(engine),
    }


def test_parity_gate_pending_adapter_equals_reader(tmp_path, monkeypatch):
    """RF-G1C.4: in_progress + gate sem decisão → GATE_PENDING nos dois.

    O engine mantém RUNNING (scheduler); a paridade §7.6 item 3 é aplicada
    na projeção (_to_step_status) — não muda semântica do engine.
    """
    fixture = _ace_fixture_gate_pending(tmp_path)
    monkeypatch.setattr("llc_wizard.data.REGISTRY", fixture["registry"])

    status_adapter = fixture["adapter"].get_status()
    by_id = {s.id: s for s in status_adapter.steps}
    assert by_id["0.5"].status == StepStatus.GATE_PENDING

    board_reader = KanbanBoardBuilder(PipelineDataReader(tmp_path)).build()
    board_adapter = KanbanBoardBuilder(fixture["adapter"]).build()

    def normalize(board):
        return {
            col.value: [c.id for c in cards]
            for col, cards in board.items()
        }

    assert normalize(board_adapter) == normalize(board_reader)
    assert [c.id for c in board_adapter[KanbanColumn.AWAITING_HUMAN]] == ["0.5"]


# ── RF-G1C.5: SLA com timestamp real da sessão ACE ───────────────────────────

def test_status_since_uses_real_ace_timestamp(tmp_path):
    """RF-G1C.5: step em in_progress às 10:00 → entered_column_at = 10:00."""
    fixture = _ace_fixture(tmp_path)
    since = fixture["adapter"].get_status_since("1")
    assert since == datetime(2026, 8, 6, 10, 0, 0)

    board = KanbanBoardBuilder(fixture["adapter"]).build()
    card = board[KanbanColumn.RUNNING][0]
    assert card.entered_column_at == datetime(2026, 8, 6, 10, 0, 0)


def test_status_since_epoch_when_no_active_session(tmp_path):
    """Sem sessão ativa → epoch (paridade com o reader)."""
    fixture = _ace_fixture(tmp_path)
    assert fixture["adapter"].get_status_since("4") == datetime.fromtimestamp(0)


# ── Demais métodos do Protocol ───────────────────────────────────────────────

def test_adapter_get_gate_for_step_from_gates_json(tmp_path):
    fixture = _ace_fixture(tmp_path)
    gate = fixture["adapter"].get_gate_for_step("1")
    assert gate is not None
    assert gate.id == "1"
    assert [i.description for i in gate.items] == ["Revisar visão"]
    assert fixture["adapter"].get_gate_for_step("999") is None


def test_adapter_pending_hitl_empty(tmp_path):
    fixture = _ace_fixture(tmp_path)
    assert fixture["adapter"].get_pending_hitl() == []


# ── Projeções (PRP-GRAPH-2B) ────────────────────────────────────────────────

def _graph_with_branches() -> Graph:
    """Grafo: A→B→C (3 nós) e A→D→E→F→G→H (6 nós) — caminho crítico = 6."""
    from llc_graph.model import Graph, GraphEdge, GraphNode, NodeKind, EdgeKind

    def _step(nid):
        return GraphNode(id=nid, kind=NodeKind.STEP,
                         requires_human=False, auto_parallelizable=False)

    graph = Graph()
    for nid in ("step-a", "step-b", "step-c", "step-d", "step-e",
                "step-f", "step-g", "step-h"):
        graph.add_node(_step(nid))
    for s, t in [("step-a", "step-b"), ("step-b", "step-c"),
                 ("step-a", "step-d"), ("step-d", "step-e"),
                 ("step-e", "step-f"), ("step-f", "step-g"),
                 ("step-g", "step-h")]:
        graph.add_edge(GraphEdge(source=s, target=t, kind=EdgeKind.DEPENDS_ON))
    return graph


def test_to_critical_path_returns_ordered_ids(tmp_path):
    """RF-G2B.4: to_critical_path(engine) → lista de node_ids em ordem."""
    engine = GraphEngine(graph=_graph_with_branches(), project_root=tmp_path)
    ids = to_critical_path(engine)
    assert ids == ["step-a", "step-d", "step-e", "step-f", "step-g",
                   "step-h"]


def test_adapter_critical_step_ids_strips_prefix(tmp_path):
    """P2b: critical_step_ids() → ids de steps no caminho crítico, sem 'step-'."""
    engine = GraphEngine(graph=_graph_with_branches(), project_root=tmp_path)
    adapter = GraphPipelineDataSource(engine)
    ids = adapter.critical_step_ids()
    assert ids == ["a", "d", "e", "f", "g", "h"]
    assert all("step-" not in i for i in ids)


def test_adapter_critical_step_ids_empty_graph(tmp_path):
    """P2b: grafo vazio → lista vazia (sem crash)."""
    from llc_graph.model import Graph

    engine = GraphEngine(graph=Graph(), project_root=tmp_path)
    assert GraphPipelineDataSource(engine).critical_step_ids() == []


def test_to_critical_path_empty(tmp_path):
    from llc_graph.model import Graph

    engine = GraphEngine(graph=Graph(), project_root=tmp_path)
    assert to_critical_path(engine) == []


def test_to_impact_map_affected_sorted(tmp_path):
    """to_impact_map: nó + afetados ordenados (determinístico)."""
    engine = GraphEngine(graph=_graph_with_branches(), project_root=tmp_path)
    result = to_impact_map(engine, "step-a")
    assert result["node"] == "step-a"
    assert "step-b" in result["affected"]
    assert "step-h" in result["affected"]
    assert result["affected"] == sorted(result["affected"])


def test_to_impact_map_unknown_node(tmp_path):
    engine = GraphEngine(graph=_graph_with_branches(), project_root=tmp_path)
    with pytest.raises(KeyError):
        to_impact_map(engine, "step-zzz")
