"""Testes para llc_graph.model — RF-G1A.1 + DoD (frozen) do PRP-GRAPH-1A.

Modelo do grafo dirigido acíclico (DAG) do pipeline LLC (ADR-0004 §2.3):
GraphNode/GraphEdge imutáveis; enums NodeKind/NodeState/EdgeKind.
"""
import dataclasses

import pytest

from llc_graph.model import (
    EdgeKind,
    Graph,
    GraphEdge,
    GraphNode,
    NodeKind,
    NodeState,
)


def test_graphnode_is_frozen():
    """RF-G1A.1: mutação em GraphNode levanta FrozenInstanceError."""
    node = GraphNode(
        id="step-5",
        kind=NodeKind.STEP,
        requires_human=False,
        auto_parallelizable=True,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        node.id = "step-6"  # type: ignore[misc]


def test_graphedge_is_frozen():
    """DoD: GraphEdge também é imutável (frozen)."""
    edge = GraphEdge(source="step-1", target="step-2", kind=EdgeKind.DEPENDS_ON)
    with pytest.raises(dataclasses.FrozenInstanceError):
        edge.kind = EdgeKind.REWORK  # type: ignore[misc]


def test_nodekind_values():
    assert {k.value for k in NodeKind} == {"step", "prp", "gate", "hitl"}


def test_nodestate_values():
    assert {k.value for k in NodeState} == {
        "pending", "ready", "running", "awaiting_human",
        "done", "failed", "skipped",
    }


def test_edgekind_values():
    assert {k.value for k in EdgeKind} == {
        "depends_on", "produces", "blocks", "rework",
    }


def test_graphnode_defaults():
    """Campos opcionais default: depends_on/produces vazios, retry_of None."""
    node = GraphNode(
        id="prp-004",
        kind=NodeKind.PRP,
        requires_human=False,
        auto_parallelizable=True,
    )
    assert node.depends_on == ()
    assert node.produces == ()
    assert node.retry_of is None


def test_graphnode_retry_of():
    node = GraphNode(
        id="step-5-retry-1",
        kind=NodeKind.STEP,
        requires_human=False,
        auto_parallelizable=True,
        retry_of="step-5",
    )
    assert node.retry_of == "step-5"


def test_graph_add_node_and_edges():
    graph = Graph()
    n1 = GraphNode("step-1", NodeKind.STEP, False, True)
    n2 = GraphNode("step-2", NodeKind.STEP, False, True)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge(GraphEdge("step-1", "step-2", EdgeKind.DEPENDS_ON))

    assert graph.node("step-1") is n1
    assert graph.node("inexistente") is None
    assert len(graph.edges) == 1
    assert graph.successors("step-1") == ["step-2"]
    assert graph.predecessors("step-2") == ["step-1"]
    assert graph.nodes_count == 2
