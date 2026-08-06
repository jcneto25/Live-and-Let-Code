"""Testes para llc_graph.builder — RF-G1A.2/3/4/7 do PRP-GRAPH-1A.

GraphBuilder unifica: ordem sequencial do REGISTRY (StepSpec.number — N1),
gates.json (nós de gate) e dependency-graph.yaml (N2 — PRPs/artefatos).
Zero mudança no harness (D2/ADR-0004).
"""
import json
from pathlib import Path

import pytest

from llc_graph.builder import GraphBuilder
from llc_graph.model import EdgeKind, NodeKind


def _registry_3_steps():
    """REGISTRY mínimo: 0.5 (com gate), 1 (com gate), 2 (sem gate)."""
    from llc_steps.models import _spec

    return {
        "0.5": _spec("0.5", "Visão + Módulos", "llc-step-0-5", "1", True, False),
        "1": _spec("1", "7 Especificações", "llc-step-1", "2", True, False),
        "2": _spec("2", "PRDs", "llc-step-2", None, True, False),
    }


def _write_gates(tmp_path: Path, gates=None) -> Path:
    gates = gates or {
        "1": {"step": 0.5, "label": "Visao", "checklist": []},
        "2": {"step": 1, "label": "7 Espec", "checklist": []},
    }
    p = tmp_path / ".ace" / "config" / "gates.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"gates": gates}), encoding="utf-8")
    return p


def _write_yaml(tmp_path: Path, artifacts: dict) -> Path:
    import yaml

    p = tmp_path / ".ace" / "dependency-graph.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump({"version": "1.0", "artifacts": artifacts}), encoding="utf-8")
    return p


def test_gates_marked_requires_human(tmp_path):
    """RF-G1A.2: step com gate em gates.json → nó GATE com requires_human=True."""
    gates = _write_gates(tmp_path)
    builder = GraphBuilder(
        project_root=tmp_path,
        registry=_registry_3_steps(),
        gates_path=gates,
    )
    graph = builder.build()

    gate_nodes = [n for n in graph.nodes.values() if n.kind == NodeKind.GATE]
    assert len(gate_nodes) == 2
    assert all(n.requires_human for n in gate_nodes)
    assert all(not n.auto_parallelizable for n in gate_nodes)


def test_n1_edges_follow_registry_order(tmp_path):
    """RF-G1A.3: arestas N1 seguem StepSpec.number (0.5 → 1 → 2)."""
    gates = _write_gates(tmp_path)
    builder = GraphBuilder(
        project_root=tmp_path,
        registry=_registry_3_steps(),
        gates_path=gates,
    )
    graph = builder.build()

    dep_edges = {(e.source, e.target) for e in graph.edges if e.kind == EdgeKind.DEPENDS_ON}
    assert ("step-0.5", "step-1") in dep_edges
    assert ("step-1", "step-2") in dep_edges
    # arestas BLOCKS: gate bloqueia o step seguinte
    block_edges = {(e.source, e.target) for e in graph.edges if e.kind == EdgeKind.BLOCKS}
    assert ("gate-1", "step-1") in block_edges
    assert ("gate-2", "step-2") in block_edges


def test_yaml_dependencies_preserved(tmp_path):
    """RF-G1A.3: nenhuma dependência do dependency-graph.yaml é perdida (N2)."""
    yaml_path = _write_yaml(tmp_path, {
        "a": {"path": "docs/a.md", "depends_on": [], "triggers_update": []},
        "b": {"path": "docs/b.md", "depends_on": ["a"], "triggers_update": []},
        "c": {"path": "docs/c.md", "depends_on": ["a", "b"], "triggers_update": []},
    })
    builder = GraphBuilder(project_root=tmp_path, yaml_path=yaml_path)
    graph = builder.build()

    # todos os artefatos viram nós (N2)
    for artifact in ("a", "b", "c"):
        node = graph.node(artifact)
        assert node is not None
        assert node.kind == NodeKind.PRP
    # todas as dependências declaradas viram arestas DEPENDS_ON
    dep_edges = {(e.source, e.target) for e in graph.edges if e.kind == EdgeKind.DEPENDS_ON}
    assert ("a", "b") in dep_edges
    assert ("a", "c") in dep_edges
    assert ("b", "c") in dep_edges


def test_orphan_nodes_detected(tmp_path):
    """RF-G1A.4: dependência apontando para nó inexistente gera warning."""
    yaml_path = _write_yaml(tmp_path, {
        "a": {"path": "docs/a.md", "depends_on": [], "triggers_update": []},
        "b": {"path": "docs/b.md", "depends_on": ["ghost"], "triggers_update": []},
    })
    builder = GraphBuilder(project_root=tmp_path, yaml_path=yaml_path)
    with pytest.warns(UserWarning) as record:
        builder.build()
    assert any("ghost" in str(w.message) for w in record)


def test_rework_creates_new_instance(tmp_path):
    """RF-G1A.7: add_rework_node → novo nó com retry_of + aresta REWORK."""
    gates = _write_gates(tmp_path)
    builder = GraphBuilder(
        project_root=tmp_path,
        registry=_registry_3_steps(),
        gates_path=gates,
    )
    graph = builder.build()

    retry = builder.add_rework_node(graph, "step-2")
    assert retry.id == "step-2-retry-1"
    assert retry.retry_of == "step-2"
    assert retry.kind == NodeKind.STEP

    rework_edges = [e for e in graph.edges if e.kind == EdgeKind.REWORK]
    assert ("step-2", "step-2-retry-1") in {(e.source, e.target) for e in rework_edges}

    # segunda iteração de rework: retry-2, sem criar ciclo
    retry2 = builder.add_rework_node(graph, "step-2")
    assert retry2.id == "step-2-retry-2"
    assert retry2.retry_of == "step-2"


def test_requires_human_gate_never_auto_parallelizable(tmp_path):
    """D3/ADR-0004: gates NUNCA auto_parallelizable (contrato ready_nodes)."""
    gates = _write_gates(tmp_path, {
        "11-SEC": {"step": 10.6, "label": "Security", "checklist": []},
    })
    builder = GraphBuilder(
        project_root=tmp_path,
        registry=_registry_3_steps(),
        gates_path=gates,
    )
    graph = builder.build()
    gate = graph.node("gate-11-SEC")
    assert gate is not None
    assert gate.requires_human
    assert not gate.auto_parallelizable
