"""Testes para llc_graph.engine — RF-G1B.1 a G1B.7 do PRP-GRAPH-1B
e RF-G2B.1 a G2B.3 do PRP-GRAPH-2B.

GraphEngine é o scheduler read-only (ADR-0004 §2.7): deriva estado e
elegibilidade de execução a partir do grafo + sessões ACE. Nunca muta
nada (projeções são queries puras — CQS).
"""
import json
from pathlib import Path

import pytest

from llc_graph.builder import GraphBuilder
from llc_graph.engine import GraphEngine
from llc_graph.model import (
    EdgeKind,
    Graph,
    GraphEdge,
    GraphNode,
    NodeKind,
    NodeState,
)
from llc_graph.state import AceStateReader


# ── Helpers de fixture ────────────────────────────────────────────────────────

def _write_index(tmp_path: Path, sessions: list[dict]):
    p = tmp_path / ".ace" / "index.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"sessions": sessions}), encoding="utf-8")


def _write_session(tmp_path: Path, session_id: str, gate_decision: str):
    """Sessão .md com <gate_result> real (não-placeholder), como o harness grava."""
    p = tmp_path / ".ace" / "sessions" / f"{session_id}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "---\nstatus: completed\n---\n\n"
        f'<!-- <gate_result step="5" decision="approved" reviewer="placeholder"> -->\n'
        f'<gate_result step="5" decision="{gate_decision}" reviewer="harness">'
        "human gate</gate_result>\n",
        encoding="utf-8",
    )
    return p


def _simple_chain() -> Graph:
    """step-1 → step-2 → step-3 (DEPENDS_ON puro, ids reais do builder)."""
    g = Graph()
    for nid in ("step-1", "step-2", "step-3"):
        g.add_node(GraphNode(id=nid, kind=NodeKind.STEP, requires_human=False,
                             auto_parallelizable=True))
    for src, tgt in (("step-1", "step-2"), ("step-2", "step-3")):
        g.add_edge(GraphEdge(source=src, target=tgt, kind=EdgeKind.DEPENDS_ON))
    return g


def _graph_with_gate() -> Graph:
    """step-5 → gate-5 (DEPENDS_ON); gate-5 → step-6 (BLOCKS)."""
    g = Graph()
    g.add_node(GraphNode(id="step-5", kind=NodeKind.STEP, requires_human=False,
                         auto_parallelizable=False))
    g.add_node(GraphNode(id="gate-5", kind=NodeKind.GATE, requires_human=True,
                         auto_parallelizable=False, depends_on=("step-5",)))
    g.add_node(GraphNode(id="step-6", kind=NodeKind.STEP, requires_human=False,
                         auto_parallelizable=False, depends_on=("step-5",)))
    g.add_edge(GraphEdge(source="step-5", target="gate-5", kind=EdgeKind.DEPENDS_ON))
    g.add_edge(GraphEdge(source="gate-5", target="step-6", kind=EdgeKind.BLOCKS))
    return g


def _make_engine(tmp_path: Path, graph: Graph, sessions: list[dict]) -> GraphEngine:
    _write_index(tmp_path, sessions)
    return GraphEngine(graph=graph, project_root=tmp_path)


# ── RF-G1B.1: ready_nodes retorna nós com deps DONE ──────────────────────────

def test_ready_nodes_returns_nodes_with_deps_done(tmp_path):
    """RF-G1B.1: step-1 DONE → step-2 READY; step-1 (DONE) não reaparece."""
    engine = _make_engine(tmp_path, _simple_chain(), [
        {"session_id": "s-1", "llc_step_id": "1", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    ready = {n.id for n in engine.ready_nodes()}
    assert "step-2" in ready
    assert "step-1" not in ready     # DONE não é elegível
    assert "step-3" not in ready     # dep de step-2 ainda pendente


def test_ready_nodes_root_node_no_deps(tmp_path):
    """Nó raiz (sem deps) fica READY imediatamente."""
    engine = _make_engine(tmp_path, _simple_chain(), [])
    ready = {n.id for n in engine.ready_nodes()}
    assert "step-1" in ready         # sem deps → satisfeitas (all([]) = True)


# ── RF-G1B.2: gates nunca auto-avançados (crítico) ───────────────────────────

def test_ready_nodes_never_auto_advances_requires_human(tmp_path):
    """RF-G1B.2: gate com deps satisfeitas → AWAITING_HUMAN, nunca READY.

    D3/ADR-0004: o scheduler não decide por humanos. O gate estaciona na
    fila do humano (AWAITING_HUMAN); a única saída é o UserDecisionWriter.
    """
    engine = _make_engine(tmp_path, _graph_with_gate(), [
        {"session_id": "s-5", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    states = {n.id: engine.node_state(n.id) for n in engine.ready_nodes()}
    assert states["gate-5"] == NodeState.AWAITING_HUMAN
    assert states["gate-5"] != NodeState.READY     # nunca auto-executável


# ── RF-G1B.3: SKIPPED equivale a DONE (delta flow — teste obrigatório) ───────

def test_ready_nodes_with_skipped_dependencies(tmp_path):
    """RF-G1B.3 (obrigatório — ADR-0004 §2.12): deps SKIPPED desbloqueiam.

    Smart Skip marca B como SKIPPED (permanece no grafo, nunca removido).
    Para fins de dependência, SKIPPED == DONE: C fica READY sem esperar B.
    """
    engine = _make_engine(tmp_path, _simple_chain(), [
        {"session_id": "s-1", "llc_step_id": "1", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
        {"session_id": "s-2", "llc_step_id": "2", "status": "skipped",
         "timestamp": "2026-08-06T11:00:00"},
    ])
    ready = {n.id for n in engine.ready_nodes()}
    assert "step-3" in ready          # step-2=SKIPPED → step-3 desbloqueado


# ── RF-G1B.4/5: impact_of propaga e é puro ───────────────────────────────────

def test_impact_of_propagates_to_all_descendants(tmp_path):
    """RF-G1B.4: step-1→step-2→step-3 → impact_of("step-1") = {2, 3}."""
    engine = _make_engine(tmp_path, _simple_chain(), [])
    assert engine.impact_of("step-1") == {"step-2", "step-3"}


def test_impact_of_is_pure(tmp_path):
    """RF-G1B.5: impacto N vezes não altera o estado do grafo (CQS)."""
    engine = _make_engine(tmp_path, _simple_chain(), [])
    nodes_before = dict(engine.graph.nodes)
    edges_before = list(engine.graph.edges)
    for _ in range(5):
        engine.impact_of("step-1")
    assert engine.graph.nodes == nodes_before
    assert engine.graph.edges == edges_before


def test_impact_of_unknown_node_raises(tmp_path):
    """impact_of em nó inexistente → KeyError (fail fast, não silent)."""
    engine = _make_engine(tmp_path, _simple_chain(), [])
    with pytest.raises(KeyError):
        engine.impact_of("GHOST")


# ── RF-G1B.6: rework como nova instância (DAG preservado) ───────────────────

def test_rework_new_instance_without_cycle(tmp_path):
    """RF-G1B.6: retry aparece READY; original (DONE) não reaparece.

    step-5 DONE → rework cria step-5-retry-1 (depends_on=(step-5,), retry_of).
    O retry fica READY (dep satisfeita); o original não volta à fila.
    """
    graph = Graph()
    graph.add_node(GraphNode(id="step-5", kind=NodeKind.STEP, requires_human=False,
                             auto_parallelizable=False))
    graph.add_node(GraphNode(id="step-5-retry-1", kind=NodeKind.STEP,
                             requires_human=False, auto_parallelizable=False,
                             depends_on=("step-5",), retry_of="step-5"))
    graph.add_edge(GraphEdge(source="step-5", target="step-5-retry-1",
                             kind=EdgeKind.REWORK))
    engine = _make_engine(tmp_path, graph, [
        {"session_id": "s-5", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    ready = {n.id for n in engine.ready_nodes()}
    assert "step-5-retry-1" in ready
    assert "step-5" not in ready      # original DONE não reaparece


# ── RF-G1B.7: determinismo ───────────────────────────────────────────────────

def test_ready_nodes_deterministic(tmp_path):
    """RF-G1B.7: mesmo estado ACE → mesmo resultado, N chamadas."""
    engine = _make_engine(tmp_path, _graph_with_gate(), [
        {"session_id": "s-5", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    first = [(n.id, engine.node_state(n.id)) for n in engine.ready_nodes()]
    for _ in range(5):
        again = [(n.id, engine.node_state(n.id)) for n in engine.ready_nodes()]
        assert again == first


# ── BLOCKS (ADR-0004 §2.4): sucessor não READY enquanto gate não aprovado ────

def test_successor_blocked_by_unapproved_gate(tmp_path):
    """§2.4: step-6 não fica READY enquanto gate-5 estiver AWAITING_HUMAN."""
    engine = _make_engine(tmp_path, _graph_with_gate(), [
        {"session_id": "s-5", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    assert engine.node_state("step-6") == NodeState.PENDING  # bloqueado pelo gate
    ready = {n.id for n in engine.ready_nodes()}
    assert "step-6" not in ready


def test_successor_ready_after_gate_approved(tmp_path):
    """§2.4: gate aprovado (<gate_result decision="approved">) → step-6 READY.

    A decisão humana é gravada no .md da sessão (UserDecisionWriter/harness);
    o engine lê o <gate_result> real, ignorando placeholders em comentários.
    """
    _write_session(tmp_path, "s-5", "approved")
    engine = _make_engine(tmp_path, _graph_with_gate(), [
        {"session_id": "s-5", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    assert engine.node_state("gate-5") == NodeState.DONE
    assert engine.node_state("step-6") == NodeState.READY
    ready = {n.id for n in engine.ready_nodes()}
    assert "step-6" in ready


def test_step_with_rejected_gate_is_failed(tmp_path):
    """Paridade §7.6: step completed + gate rejeitado → FAILED (não DONE).

    Regressão (revisão GRAPH-1C): o engine retornava DONE para o step sem
    consultar a decisão do gate — o reader mostra FAILED (rework).
    """
    _write_session(tmp_path, "s-5", "rejected")
    engine = _make_engine(tmp_path, _graph_with_gate(), [
        {"session_id": "s-5", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    assert engine.node_state("step-5") == NodeState.FAILED
    assert engine.node_state("gate-5") == NodeState.FAILED
    assert engine.node_state("step-6") == NodeState.PENDING  # BLOCKS mantém


def test_step_with_approved_gate_stays_done(tmp_path):
    """Paridade §7.6: completed + gate aprovado → DONE (inalterado)."""
    _write_session(tmp_path, "s-5", "approved")
    engine = _make_engine(tmp_path, _graph_with_gate(), [
        {"session_id": "s-5", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    assert engine.node_state("step-5") == NodeState.DONE
    assert engine.node_state("gate-5") == NodeState.DONE
    assert engine.node_state("step-6") == NodeState.READY


def test_step_gate_decision_helper(tmp_path):
    """step_gate_decision() expõe a decisão do gate do step (paridade §7.6)."""
    _write_session(tmp_path, "s-5", "rejected")
    engine = _make_engine(tmp_path, _graph_with_gate(), [
        {"session_id": "s-5", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    assert engine.step_gate_decision("5") == "rejected"
    assert engine.step_gate_decision("6") is None  # step sem gate
    assert engine.step_gate_decision("999") is None  # step inexistente


def test_node_state_unknown_node_raises(tmp_path):
    """node_state em nó fora do grafo → KeyError (contrato fail-fast)."""
    engine = _make_engine(tmp_path, _simple_chain(), [])
    with pytest.raises(KeyError):
        engine.node_state("step-999")


# ── RF-G1C.5: session_timestamp (SLA do Kanban) ──────────────────────────────

def test_session_timestamp_active_session(tmp_path):
    """RF-G1C.5: timestamp real da sessão ativa (in_progress)."""
    import datetime as dt

    engine = _make_engine(tmp_path, _simple_chain(), [
        {"session_id": "s-1", "llc_step_id": "1", "status": "in_progress",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    assert engine.session_timestamp("1") == dt.datetime(2026, 8, 6, 10, 0, 0)


def test_session_timestamp_ignores_skipped_only(tmp_path):
    """Sessão apenas skipped não conta como ativa → epoch."""
    import datetime as dt

    engine = _make_engine(tmp_path, _simple_chain(), [
        {"session_id": "s-1", "llc_step_id": "1", "status": "skipped",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    assert engine.session_timestamp("1") == dt.datetime.fromtimestamp(0)


def test_session_timestamp_missing_index_epoch(tmp_path):
    """index.json ausente → epoch, sem exceção."""
    import datetime as dt

    engine = _make_engine(tmp_path, _simple_chain(), [])
    assert engine.session_timestamp("1") == dt.datetime.fromtimestamp(0)


def test_session_timestamp_invalid_ts_epoch(tmp_path):
    """Timestamp malformado → epoch, sem exceção."""
    import datetime as dt

    engine = _make_engine(tmp_path, _simple_chain(), [
        {"session_id": "s-1", "llc_step_id": "1", "status": "completed",
         "timestamp": "nao-iso"},
    ])
    assert engine.session_timestamp("1") == dt.datetime.fromtimestamp(0)


def test_gate_approved_in_builder_graph(tmp_path):
    """Gate aprovado em grafo do GraphBuilder (nós SEM depends_on).

    Regressão: o builder cria nós de gate sem depends_on (estrutura vive nas
    arestas). O engine deve derivar o step gateado da aresta DEPENDS_ON de
    entrada — senão gates nunca aprovam e o contrato BLOCKS (ADR-0004 §2.4)
    bloqueia os sucessores para sempre.
    """
    import json as _json

    # REGISTRY mínimo: 0.5 (gate 1), 1 (sem gate) — builder cria as arestas
    from llc_steps.models import _spec

    registry = {
        "0.5": _spec("0.5", "Visão", "llc-step-0-5", "1", True, False),
        "1": _spec("1", "7 Especificações", "llc-step-1", None, True, False),
    }
    gates_path = tmp_path / ".ace" / "config" / "gates.json"
    gates_path.parent.mkdir(parents=True, exist_ok=True)
    gates_path.write_text(_json.dumps({"gates": {
        "1": {"step": 0.5, "label": "Visao", "checklist": []},
    }}), encoding="utf-8")
    builder = GraphBuilder(project_root=tmp_path, registry=registry,
                           gates_path=gates_path)
    graph = builder.build()

    # step-0.5 completed + gate-1 aprovado na sessão
    _write_index(tmp_path, [
        {"session_id": "s-05", "llc_step_id": "0.5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    _write_session(tmp_path, "s-05", "approved")
    engine = GraphEngine(graph=graph, project_root=tmp_path)

    assert engine.node_state("gate-1") == NodeState.DONE
    assert engine.node_state("step-1") == NodeState.READY   # BLOCKS liberado
    ready = {n.id for n in engine.ready_nodes()}
    assert "step-1" in ready


# ── PRP-GRAPH-2A: parallel_frontier() (ADR-0004 §2.7, Q2) ────────────────────
# RF-G2A.1-2A.5 — dados puros agnósticos de runtime: auto_parallelizable,
# independentes entre si, subset de ready_nodes, sem requires_human, puro.

def _graph_with_prps() -> Graph:
    """PRPs (auto_parallelizable=True) + step com gate (não paralelizável).

    prp-001 → prp-002 (DEPENDS_ON); prp-003 independente.
    step-5 (com gate) → gate-5 → BLOCKS step-6 — nenhum auto_parallelizable.
    """
    g = Graph()
    for pid in ("prp-001", "prp-002", "prp-003"):
        g.add_node(GraphNode(id=pid, kind=NodeKind.PRP, requires_human=False,
                             auto_parallelizable=True))
    g.add_edge(GraphEdge(source="prp-001", target="prp-002",
                         kind=EdgeKind.DEPENDS_ON))
    g.add_node(GraphNode(id="step-5", kind=NodeKind.STEP, requires_human=False,
                         auto_parallelizable=False))
    g.add_node(GraphNode(id="gate-5", kind=NodeKind.GATE, requires_human=True,
                         auto_parallelizable=False))
    g.add_node(GraphNode(id="step-6", kind=NodeKind.STEP, requires_human=False,
                         auto_parallelizable=False))
    g.add_edge(GraphEdge(source="step-5", target="gate-5", kind=EdgeKind.DEPENDS_ON))
    g.add_edge(GraphEdge(source="gate-5", target="step-6", kind=EdgeKind.BLOCKS))
    return g


def _make_graph(nodes: list[GraphNode], edges: list[tuple[str, str]]) -> Graph:
    """Grafo puro manual: nós + arestas DEPENDS_ON."""
    graph = Graph()
    for n in nodes:
        graph.add_node(n)
    for source, target in edges:
        graph.add_edge(GraphEdge(source=source, target=target,
                                 kind=EdgeKind.DEPENDS_ON))
    return graph


def _has_edge_between(graph: Graph, a: str, b: str) -> bool:
    """True se existe aresta (qualquer direção/kind) entre a e b."""
    return any(
        (e.source == a and e.target == b) or (e.source == b and e.target == a)
        for e in graph.edges
    )


# ── RF-G2A.1: apenas auto_parallelizable=True ────────────────────────────────
def test_parallel_frontier_only_auto_parallelizable(tmp_path):
    """RF-G2A.1: frontier contém apenas nós auto_parallelizable=True.

    No grafo do PRP, só PRPs são auto_parallelizable — steps com gate e
    gates (requires_human) ficam de fora.
    """
    engine = _make_engine(tmp_path, _graph_with_prps(), [])
    frontier = engine.parallel_frontier()
    assert frontier, "deve haver candidatos auto_parallelizable prontos"
    assert all(n.auto_parallelizable for n in frontier)
    assert all(n.id not in ("step-5", "gate-5", "step-6") for n in frontier)


# ── RF-G2A.2: independência mútua (crítico) ──────────────────────────────────
def test_parallel_frontier_nodes_mutually_independent(tmp_path):
    """RF-G2A.2: nenhum par da frontier tem aresta entre si (qualquer kind)."""
    engine = _make_engine(tmp_path, _graph_with_prps(), [])
    frontier = engine.parallel_frontier()
    ids = [n.id for n in frontier]
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            assert not _has_edge_between(engine.graph, a, b), \
                f"{a} e {b} têm aresta entre si — não são independentes"


def test_parallel_frontier_dependent_prps_never_together(tmp_path):
    """RF-G2A.2: prp-001 → prp-002 nunca aparecem juntos na frontier.

    prp-002 depende de prp-001 (não satisfeita) → PENDING, fora da frontier;
    a frontier contém apenas prp-001 e prp-003 (raízes independentes).
    """
    engine = _make_engine(tmp_path, _graph_with_prps(), [])
    frontier_ids = {n.id for n in engine.parallel_frontier()}
    assert "prp-001" in frontier_ids
    assert "prp-003" in frontier_ids
    assert not ({"prp-001", "prp-002"} <= frontier_ids)


# ── RF-G2A.3: subset de ready_nodes() ────────────────────────────────────────
def test_parallel_frontier_subset_of_ready_nodes(tmp_path):
    """RF-G2A.3: todo elemento da frontier também está em ready_nodes()."""
    engine = _make_engine(tmp_path, _graph_with_prps(), [])
    ready_ids = {n.id for n in engine.ready_nodes()}
    frontier_ids = {n.id for n in engine.parallel_frontier()}
    assert frontier_ids <= ready_ids
    assert frontier_ids, "frontier não pode ser vazia quando há candidatos"


# ── RF-G2A.4: requires_human nunca na frontier ───────────────────────────────
def test_parallel_frontier_excludes_requires_human(tmp_path):
    """RF-G2A.4: gate AWAITING_HUMAN (requires_human) nunca na frontier.

    step-5 completed → gate-5 estaciona na fila do humano; apesar de estar
    em ready_nodes() (AWAITING_HUMAN), NÃO é auto_parallelizable nem
    auto-executável — a frontier o exclui.
    """
    engine = _make_engine(tmp_path, _graph_with_prps(), [
        {"session_id": "s-5", "llc_step_id": "5", "status": "completed",
         "timestamp": "2026-08-06T10:00:00"},
    ])
    assert engine.node_state("gate-5") == NodeState.AWAITING_HUMAN
    assert "gate-5" in {n.id for n in engine.ready_nodes()}
    frontier = engine.parallel_frontier()
    assert all(not n.requires_human for n in frontier)
    assert all(n.id != "gate-5" for n in frontier)


# ── RF-G2A.5: puro e determinístico (CQS) ────────────────────────────────────
def test_parallel_frontier_pure_and_deterministic(tmp_path):
    """RF-G2A.5: N chamadas → mesmo resultado e grafo inalterado (CQS)."""
    engine = _make_engine(tmp_path, _graph_with_prps(), [])
    nodes_before = dict(engine.graph.nodes)
    edges_before = list(engine.graph.edges)
    first = [(n.id, n.auto_parallelizable) for n in engine.parallel_frontier()]
    for _ in range(5):
        again = [(n.id, n.auto_parallelizable) for n in engine.parallel_frontier()]
        assert again == first
    assert engine.graph.nodes == nodes_before
    assert engine.graph.edges == edges_before


# ── Integração com GraphBuilder (grafo real N1+N2) ───────────────────────────
def test_parallel_frontier_with_builder_graph(tmp_path):
    """Frontier no grafo do builder: PRPs N2 independentes entram, gates não."""
    import json as _json

    from llc_steps.models import _spec

    registry = {
        "0.5": _spec("0.5", "Visão", "llc-step-0-5", "1", True, False),
        "1": _spec("1", "7 Especificações", "llc-step-1", None, True, False),
    }
    # dependency-graph.yaml com 2 artefatos independentes (PRPs N2)
    yaml_path = tmp_path / ".ace" / "dependency-graph.yaml"
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text("""\
artifacts:
  prp-alpha:
    depends_on: []
    path: docs/prps/PRP-ALPHA.md
  prp-beta:
    depends_on: []
    path: docs/prps/PRP-BETA.md
""", encoding="utf-8")
    builder = GraphBuilder(project_root=tmp_path, registry=registry)
    graph = builder.build()
    engine = GraphEngine(graph=graph, project_root=tmp_path)

    frontier_ids = {n.id for n in engine.parallel_frontier()}
    assert "prp-alpha" in frontier_ids
    assert "prp-beta" in frontier_ids
    assert all("gate" not in nid for nid in frontier_ids)
    # ambos independentes entre si
    assert not _has_edge_between(graph, "prp-alpha", "prp-beta")


# ═══════════════════════════════════════════════════════════════════════════
# critical_path() — PRP-GRAPH-2B (RF-G2B.1 a G2B.3)
# ═══════════════════════════════════════════════════════════════════════════

def _step(nid: str) -> GraphNode:
    return GraphNode(id=nid, kind=NodeKind.STEP,
                     requires_human=False, auto_parallelizable=False)


def _gate(nid: str) -> GraphNode:
    return GraphNode(id=nid, kind=NodeKind.GATE,
                     requires_human=True, auto_parallelizable=False)


def test_critical_path_longest_branch(tmp_path):
    """RF-G2B.1: entre dois caminhos (3 e 6 nós), retorna o de comprimento 6."""
    # A → B → C (3 nós) e A → D → E → F → G → H (6 nós)
    nodes = [_step("step-a"), _step("step-b"), _step("step-c"),
             _step("step-d"), _step("step-e"), _step("step-f"),
             _step("step-g"), _step("step-h")]
    edges = [("step-a", "step-b"), ("step-b", "step-c"),
             ("step-a", "step-d"), ("step-d", "step-e"),
             ("step-e", "step-f"), ("step-f", "step-g"),
             ("step-g", "step-h")]
    graph = _make_graph(nodes, edges)
    engine = GraphEngine(graph=graph, project_root=tmp_path)

    path = engine.critical_path()
    ids = [n.id for n in path]
    assert len(path) == 6
    assert ids == ["step-a", "step-d", "step-e", "step-f", "step-g",
                   "step-h"]


def test_critical_path_includes_gates(tmp_path):
    """RF-G2B.2: gates entram no caminho crítico (têm custo de espera).

    Gate tem peso > 1 (espera humana), então A → gate → C vence A → B → C.
    """
    nodes = [_step("step-a"), _step("step-b"), _step("step-c"),
             _gate("gate-a")]
    edges = [("step-a", "step-b"), ("step-b", "step-c"),
             ("step-a", "gate-a"), ("gate-a", "step-c")]
    graph = _make_graph(nodes, edges)
    engine = GraphEngine(graph=graph, project_root=tmp_path)

    path = engine.critical_path()
    ids = [n.id for n in path]
    assert "gate-a" in ids  # gate incluído por seu peso
    assert ids[0] == "step-a" and ids[-1] == "step-c"
    assert ids.index("gate-a") > ids.index("step-a")


def test_critical_path_skipped_weight_zero(tmp_path):
    """Nós SKIPPED têm peso 0 — não alongam o caminho crítico."""
    _write_index(tmp_path, [
        {"session_id": "s1", "llc_step_id": "1", "status": "skipped",
         "timestamp": "2026-08-01T00:00:00"},
        {"session_id": "s2", "llc_step_id": "2", "status": "skipped",
         "timestamp": "2026-08-01T00:00:00"},
        {"session_id": "s3", "llc_step_id": "3", "status": "skipped",
         "timestamp": "2026-08-01T00:00:00"},
    ])
    # Cadeia longa de SKIPPED (step-1..3, peso 0) vs. caminho com nó ativo
    # step-1 → step-x (peso 1). A cadeia skipped não alonga o caminho crítico.
    nodes = [_step("step-1"), _step("step-2"), _step("step-3"),
             _step("step-x")]
    edges = [("step-1", "step-2"), ("step-2", "step-3"),
             ("step-1", "step-x")]
    graph = _make_graph(nodes, edges)
    engine = GraphEngine(graph=graph, project_root=tmp_path)

    path = engine.critical_path()
    ids = [n.id for n in path]
    # peso: step-1→step-2→step-3 = 0; step-1→step-x = 1 → este é o crítico
    assert ids == ["step-1", "step-x"]


def test_critical_path_pure_and_deterministic(tmp_path):
    """RF-G2B.3: pureza — múltiplas chamadas, mesmo resultado, estado inalterado."""
    nodes = [_step("step-a"), _step("step-b"), _step("step-c"), _step("step-d")]
    edges = [("step-a", "step-b"), ("step-b", "step-c"),
             ("step-b", "step-d")]
    graph = _make_graph(nodes, edges)
    engine = GraphEngine(graph=graph, project_root=tmp_path)

    nodes_before = dict(engine.graph.nodes)
    edges_before = list(engine.graph.edges)
    first = [n.id for n in engine.critical_path()]
    for _ in range(5):
        assert [n.id for n in engine.critical_path()] == first
    assert engine.graph.nodes == nodes_before
    assert engine.graph.edges == edges_before


def test_critical_path_empty_graph(tmp_path):
    """Grafo vazio → caminho vazio."""
    engine = GraphEngine(graph=Graph(), project_root=tmp_path)
    assert engine.critical_path() == []


def test_critical_path_single_node(tmp_path):
    """Grafo com um único nó → o próprio nó."""
    graph = _make_graph([_step("step-a")], [])
    engine = GraphEngine(graph=graph, project_root=tmp_path)
    assert [n.id for n in engine.critical_path()] == ["step-a"]


def test_critical_path_cycle_raises(tmp_path):
    """Ciclo viola o invariante DAG (ADR-0004 §2.5) → ValueError claro."""
    nodes = [_step("step-a"), _step("step-b"), _step("step-c")]
    edges = [("step-a", "step-b"), ("step-b", "step-c"),
             ("step-c", "step-a")]
    graph = _make_graph(nodes, edges)
    engine = GraphEngine(graph=graph, project_root=tmp_path)
    with pytest.raises(ValueError, match="ciclo"):
        engine.critical_path()


def test_critical_path_double_count_regression(tmp_path):
    """Regressão (review): pesos contam exatamente uma vez por nó.

    Bug: `cand = dist[nid] + weight(succ)` somava o peso de succ na
    relaxação E de novo quando succ era processado — double-count que
    inflava dist e trocava a escolha do caminho quando gates/skipped
    misturados empatavam. Fix: `cand = dist[nid]` (peso de succ entra
    apenas no processamento).

    Cenário: gate-a→gate-b (peso 2+2=4) vs step-k→x→y→z com k SKIPPED
    (peso 0+1+1+1=3). Correto: gates vencem (4 > 3). Com double-count,
    a cadeia skipped inflava para 6 e empatava, trocando a escolha.
    """
    _write_index(tmp_path, [
        {"session_id": "sk", "llc_step_id": "k", "status": "skipped",
         "timestamp": "2026-08-01T00:00:00"},
    ])
    nodes = [_gate("gate-a"), _gate("gate-b"),
             _step("step-k"), _step("step-x"), _step("step-y"),
             _step("step-z")]
    edges = [("gate-a", "gate-b"), ("step-k", "step-x"),
             ("step-x", "step-y"), ("step-y", "step-z")]
    graph = _make_graph(nodes, edges)
    engine = GraphEngine(graph=graph, project_root=tmp_path)

    path = [n.id for n in engine.critical_path()]
    assert path == ["gate-a", "gate-b"]  # 4 > 3 — gates, não a cadeia skipped
